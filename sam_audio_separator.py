"""
SAM Audio Integration - Meta's foundation model for sound isolation
Provides text-prompted audio separation as an alternative to Demucs
"""

import os
import sys
from pathlib import Path
from typing import Optional, List, Dict
import torch
import torchaudio


class SAMAudioSeparator:
    """
    Wrapper for Meta's SAM Audio model
    Isolates sounds using text descriptions
    """

    def __init__(self, model_size: str = "large", device: str = "auto"):
        """
        Initialize SAM Audio separator

        Args:
            model_size: Model size - "small", "base", or "large"
            device: Device to use - "auto", "cuda", or "cpu"
        """
        self.model_size = model_size
        self.model_name = f"facebook/sam-audio-{model_size}"

        # Determine device
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        self.model = None
        self.processor = None
        self.available = False

        # Try to import and initialize
        try:
            from sam_audio import SAMAudio, SAMAudioProcessor

            print(f"Loading SAM Audio ({model_size}) model...")
            self.model = SAMAudio.from_pretrained(self.model_name)
            self.processor = SAMAudioProcessor.from_pretrained(self.model_name)

            self.model = self.model.eval()
            if self.device == "cuda":
                self.model = self.model.cuda()

            self.available = True
            print(f"✓ SAM Audio loaded successfully on {self.device}")

        except ImportError:
            print("⚠ SAM Audio not installed")
            print("Install: git clone https://github.com/facebookresearch/sam-audio && cd sam-audio && pip install .")
            self.available = False

        except Exception as e:
            print(f"⚠ Failed to load SAM Audio: {e}")
            print("Note: SAM Audio requires Hugging Face authentication")
            print("Run: huggingface-cli login")
            self.available = False

    def separate(self,
                 audio_file: str,
                 description: str,
                 output_dir: str = ".",
                 predict_spans: bool = False,
                 reranking_candidates: int = 1) -> Dict[str, str]:
        """
        Separate audio using text description

        Args:
            audio_file: Path to input audio file
            description: Text description of sound to isolate
                        Examples:
                        - "A guitar playing"
                        - "A bass guitar"
                        - "A drum kit"
                        - "Electric guitar solo"
                        - "Vocal singing"
            output_dir: Directory to save output files
            predict_spans: Whether to predict when sound occurs
            reranking_candidates: Number of separation attempts to rank

        Returns:
            Dictionary with paths to output files:
            - 'target': Isolated sound matching description
            - 'residual': Everything else
        """
        if not self.available:
            raise RuntimeError("SAM Audio is not available")

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Process audio
        print(f"Processing: {audio_file}")
        print(f"Isolating: {description}")

        batch = self.processor(
            audios=[audio_file],
            descriptions=[description],
        )

        if self.device == "cuda":
            batch = batch.to("cuda")

        # Separate
        with torch.inference_mode():
            result = self.model.separate(
                batch,
                predict_spans=predict_spans,
                reranking_candidates=reranking_candidates
            )

        # Save outputs
        sample_rate = self.processor.audio_sampling_rate

        target_path = os.path.join(output_dir, "target.wav")
        residual_path = os.path.join(output_dir, "residual.wav")

        torchaudio.save(target_path, result.target.cpu(), sample_rate)
        torchaudio.save(residual_path, result.residual.cpu(), sample_rate)

        print(f"✓ Saved target to: {target_path}")
        print(f"✓ Saved residual to: {residual_path}")

        return {
            'target': target_path,
            'residual': residual_path
        }

    def separate_multiple(self,
                         audio_file: str,
                         descriptions: List[str],
                         output_dir: str = ".") -> Dict[str, str]:
        """
        Separate multiple sounds from the same audio file

        Args:
            audio_file: Path to input audio file
            descriptions: List of descriptions to isolate
            output_dir: Directory to save output files

        Returns:
            Dictionary mapping descriptions to output file paths
        """
        if not self.available:
            raise RuntimeError("SAM Audio is not available")

        os.makedirs(output_dir, exist_ok=True)

        results = {}

        for i, description in enumerate(descriptions):
            print(f"\n[{i+1}/{len(descriptions)}] Isolating: {description}")

            # Create subdirectory for this separation
            desc_safe = "".join(c for c in description if c.isalnum() or c in (' ', '-', '_'))
            desc_safe = desc_safe.replace(' ', '_')
            sub_dir = os.path.join(output_dir, f"{i+1}_{desc_safe}")

            outputs = self.separate(
                audio_file=audio_file,
                description=description,
                output_dir=sub_dir
            )

            results[description] = outputs['target']

        return results


def get_instrument_descriptions() -> Dict[str, str]:
    """
    Get common instrument descriptions for Clone Hero charts

    Returns:
        Dictionary of instrument names to SAM Audio descriptions
    """
    return {
        'guitar': "An electric guitar playing",
        'bass': "A bass guitar playing",
        'drums': "A drum kit playing",
        'vocals': "A person singing",
        'lead_guitar': "An electric guitar solo",
        'rhythm_guitar': "A rhythm guitar playing chords",
        'synth': "A synthesizer playing",
        'piano': "A piano playing",
        'acoustic_guitar': "An acoustic guitar playing",
    }


def main():
    """Test SAM Audio separator"""
    import argparse

    parser = argparse.ArgumentParser(description="SAM Audio separator for Clone Hero")
    parser.add_argument("audio_file", help="Input audio file")
    parser.add_argument("--description", "-d",
                       default="An electric guitar playing",
                       help="Description of sound to isolate")
    parser.add_argument("--output", "-o", default="sam_output",
                       help="Output directory")
    parser.add_argument("--model-size", choices=["small", "base", "large"],
                       default="large", help="Model size")
    parser.add_argument("--presets", action="store_true",
                       help="Separate all common instruments")

    args = parser.parse_args()

    # Initialize separator
    separator = SAMAudioSeparator(model_size=args.model_size)

    if not separator.available:
        print("\n❌ SAM Audio is not available!")
        print("\nTo install SAM Audio:")
        print("1. Clone: git clone https://github.com/facebookresearch/sam-audio")
        print("2. Install: cd sam-audio && pip install .")
        print("3. Authenticate: huggingface-cli login")
        print("4. Request access: https://huggingface.co/facebook/sam-audio-large")
        return

    if args.presets:
        # Separate all common instruments
        descriptions = list(get_instrument_descriptions().values())
        print(f"\nSeparating {len(descriptions)} instruments...")

        results = separator.separate_multiple(
            audio_file=args.audio_file,
            descriptions=descriptions,
            output_dir=args.output
        )

        print("\n" + "="*60)
        print("SEPARATION COMPLETE")
        print("="*60)
        for desc, path in results.items():
            print(f"  {desc:30s} -> {path}")

    else:
        # Single separation
        results = separator.separate(
            audio_file=args.audio_file,
            description=args.description,
            output_dir=args.output
        )

        print("\n" + "="*60)
        print("SEPARATION COMPLETE")
        print("="*60)
        print(f"  Target:   {results['target']}")
        print(f"  Residual: {results['residual']}")


if __name__ == "__main__":
    main()
