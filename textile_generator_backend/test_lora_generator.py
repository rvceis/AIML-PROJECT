"""
Test script for LoRA-based textile generator
Tests all three styles: bandhani, batik, ikat
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.lora_generator import LoRATextileGenerator
import torch
from PIL import Image
import time

def test_lora_generator():
    """Test the LoRA generator with all three styles"""
    
    print("="*80)
    print("TESTING LORA TEXTILE GENERATOR")
    print("="*80)
    
    # Check CUDA
    print(f"\nCUDA Available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
    
    # Initialize generator
    print("\n" + "="*80)
    print("Initializing LoRA Generator...")
    print("="*80)
    
    lora_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'textile_loras_trained'
    )
    print(f"LoRA path: {lora_path}")
    
    try:
        generator = LoRATextileGenerator(lora_base_path=lora_path)
        print("✅ Generator initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize generator: {e}")
        return False
    
    # Test prompts for each style
    test_cases = [
        {
            "style": "bandhani",
            "prompt": "vibrant red and gold with small circular dots",
            "color_1": "red",
            "color_2": "gold"
        },
        {
            "style": "batik",
            "prompt": "intricate floral design with blue and white colors",
            "color_1": "blue",
            "color_2": "white"
        },
        {
            "style": "ikat",
            "prompt": "geometric zigzag pattern with purple and orange",
            "color_1": "purple",
            "color_2": "orange"
        }
    ]
    
    # Create output directory
    output_dir = os.path.join(os.path.dirname(__file__), 'test_outputs')
    os.makedirs(output_dir, exist_ok=True)
    
    results = []
    
    # Test each style
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"TEST {i}/3: {test_case['style'].upper()}")
        print("="*80)
        
        print(f"Prompt: {test_case['prompt']}")
        print(f"Colors: {test_case['color_1']}, {test_case['color_2']}")
        
        try:
            # Start timer
            start_time = time.time()
            
            # Generate image
            print(f"\nGenerating {test_case['style']} pattern...")
            image, seed = generator.generate(
                prompt=test_case['prompt'],
                style=test_case['style'],
                color_1=test_case['color_1'],
                color_2=test_case['color_2'],
                num_inference_steps=20,  # Reduced for faster testing
                seed=42 + i  # Consistent seeds for reproducibility
            )
            
            # Calculate time
            elapsed = time.time() - start_time
            
            # Save image
            filename = f"test_{test_case['style']}_{seed}.png"
            filepath = os.path.join(output_dir, filename)
            image.save(filepath)
            
            print(f"✅ SUCCESS!")
            print(f"   Time: {elapsed:.2f}s")
            print(f"   Seed: {seed}")
            print(f"   Size: {image.size}")
            print(f"   Saved: {filepath}")
            
            results.append({
                'style': test_case['style'],
                'success': True,
                'time': elapsed,
                'seed': seed,
                'filepath': filepath
            })
            
        except Exception as e:
            print(f"❌ FAILED: {e}")
            import traceback
            traceback.print_exc()
            
            results.append({
                'style': test_case['style'],
                'success': False,
                'error': str(e)
            })
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    success_count = sum(1 for r in results if r['success'])
    total_count = len(results)
    
    print(f"\nTests Passed: {success_count}/{total_count}")
    
    for result in results:
        status = "✅" if result['success'] else "❌"
        print(f"\n{status} {result['style'].upper()}")
        if result['success']:
            print(f"   Time: {result['time']:.2f}s")
            print(f"   Seed: {result['seed']}")
            print(f"   File: {result['filepath']}")
        else:
            print(f"   Error: {result['error']}")
    
    if success_count == total_count:
        print("\n🎉 All tests passed!")
        print(f"📁 Output directory: {output_dir}")
        return True
    else:
        print(f"\n⚠️  {total_count - success_count} test(s) failed")
        return False


def test_memory_cleanup():
    """Test memory cleanup functionality"""
    print("\n" + "="*80)
    print("TESTING MEMORY CLEANUP")
    print("="*80)
    
    lora_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'textile_loras_trained'
    )
    
    generator = LoRATextileGenerator(lora_base_path=lora_path)
    
    # Load all styles
    print("\nLoading all three styles...")
    for style in ['bandhani', 'batik', 'ikat']:
        generator.load_style_pipeline(style)
        print(f"  ✅ Loaded {style}")
    
    print(f"\nLoaded styles: {generator.get_loaded_styles()}")
    
    # Unload one
    print("\nUnloading 'batik'...")
    generator.unload_style_pipeline('batik')
    print(f"Remaining styles: {generator.get_loaded_styles()}")
    
    # Unload all
    print("\nUnloading all pipelines...")
    generator.unload_all_pipelines()
    print(f"Loaded styles: {generator.get_loaded_styles()}")
    
    print("\n✅ Memory cleanup test passed!")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("LORA TEXTILE GENERATOR TEST SUITE")
    print("="*80)
    
    # Test main generation
    success = test_lora_generator()
    
    # Test memory cleanup
    if success:
        try:
            test_memory_cleanup()
        except Exception as e:
            print(f"\n⚠️  Memory cleanup test failed: {e}")
    
    print("\n" + "="*80)
    print("TEST SUITE COMPLETE")
    print("="*80)
