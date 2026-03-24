"""
FinBERT Sentiment Scorer — GPU-accelerated financial sentiment analysis.

Uses ProsusAI/finbert from HuggingFace to classify text as
positive / negative / neutral.  Supports:
- GPU (CUDA) with full float32
- CPU with float16 quantization for reduced memory
- Batch processing (default batch size 32)
- Singleton model caching to avoid reload per request
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from app.config import settings

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════
# Data Classes
# ═══════════════════════════════════════════════════════

@dataclass
class SentimentResult:
    """Sentiment probabilities for a single text."""
    positive: float
    negative: float
    neutral: float

    @property
    def label(self) -> str:
        """Return the dominant sentiment label."""
        scores = {"positive": self.positive, "negative": self.negative, "neutral": self.neutral}
        return max(scores, key=scores.get)

    @property
    def composite_score(self) -> float:
        """
        Composite score in [-1, +1] range.
        +1 = fully positive, -1 = fully negative, 0 = neutral.
        """
        return self.positive - self.negative

    def to_dict(self) -> dict:
        return {
            "positive": round(self.positive, 4),
            "negative": round(self.negative, 4),
            "neutral": round(self.neutral, 4),
            "label": self.label,
            "composite_score": round(self.composite_score, 4),
        }


# ═══════════════════════════════════════════════════════
# Singleton FinBERT Scorer
# ═══════════════════════════════════════════════════════

class FinBERTScorer:
    """
    Singleton FinBERT model wrapper.

    The model is loaded lazily on the first call and cached globally.
    On GPU: float32 for maximum accuracy.
    On CPU: float16 quantization for reduced memory usage.
    """

    _instance: FinBERTScorer | None = None

    def __new__(cls) -> FinBERTScorer:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._model = None
        self._tokenizer = None
        self._device = None
        self._batch_size = settings.finbert_batch_size
        self._model_name = settings.finbert_model_name
        self._initialized = True

    def _load_model(self) -> None:
        """Load the FinBERT model and tokenizer."""
        if self._model is not None:
            return

        logger.info(f"Loading FinBERT model: {self._model_name}")

        self._tokenizer = AutoTokenizer.from_pretrained(self._model_name)

        # Determine device and precision
        if torch.cuda.is_available():
            self._device = torch.device("cuda")
            self._model = AutoModelForSequenceClassification.from_pretrained(
                self._model_name
            ).to(self._device)
            logger.info("FinBERT loaded on GPU (float32)")
        else:
            self._device = torch.device("cpu")
            self._model = AutoModelForSequenceClassification.from_pretrained(
                self._model_name,
                torch_dtype=torch.float16,
            ).to(self._device)
            logger.info("FinBERT loaded on CPU (float16 quantized)")

        self._model.eval()

        # Label mapping for ProsusAI/finbert
        # Output order: positive=0, negative=1, neutral=2
        self._label_map = {0: "positive", 1: "negative", 2: "neutral"}

    def score_single(self, text: str) -> SentimentResult:
        """Score a single text string."""
        results = self.score_batch([text])
        return results[0]

    @torch.no_grad()
    def score_batch(self, texts: list[str]) -> list[SentimentResult]:
        """
        Batch-score multiple texts for sentiment.

        Args:
            texts: list of text strings to classify

        Returns:
            list of SentimentResult with probabilities
        """
        self._load_model()

        results: list[SentimentResult] = []

        # Process in chunks of batch_size
        for i in range(0, len(texts), self._batch_size):
            batch_texts = texts[i : i + self._batch_size]

            # Tokenize
            encodings = self._tokenizer(
                batch_texts,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt",
            ).to(self._device)

            # Forward pass
            outputs = self._model(**encodings)
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)

            # Convert to SentimentResult
            for prob_row in probs.cpu().numpy():
                results.append(
                    SentimentResult(
                        positive=float(prob_row[0]),
                        negative=float(prob_row[1]),
                        neutral=float(prob_row[2]),
                    )
                )

        return results

    @property
    def is_loaded(self) -> bool:
        """Check if the model is loaded."""
        return self._model is not None

    @property
    def device_name(self) -> str:
        """Return the device the model is on."""
        if self._device is None:
            return "not loaded"
        return str(self._device)


# ═══════════════════════════════════════════════════════
# Module-level convenience functions
# ═══════════════════════════════════════════════════════

_scorer: FinBERTScorer | None = None


def get_scorer() -> FinBERTScorer:
    """Get the singleton FinBERT scorer instance."""
    global _scorer
    if _scorer is None:
        _scorer = FinBERTScorer()
    return _scorer


def score_texts(texts: list[str]) -> list[SentimentResult]:
    """Score a list of texts using the cached FinBERT model."""
    return get_scorer().score_batch(texts)


def score_text(text: str) -> SentimentResult:
    """Score a single text using the cached FinBERT model."""
    return get_scorer().score_single(text)
