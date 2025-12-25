# Prompt Flow Analysis - Textile Generator Backend

## Summary
**YES - The prompt IS modified between frontend and model.** The user's prompt is enhanced with style descriptions, color information, and quality keywords before being sent to the model.

---

## Complete Prompt Flow

### 1. **Frontend → Backend API** (`frontend/src/services/api.ts`)
```
User enters: "a beautiful floral design"

Frontend sends to /api/generate:
{
  "prompt": "a beautiful floral design",
  "style": "bandhani",
  "color_1": "blue",
  "color_2": "white",
  "seed": null
}
```
✅ **No modification at this stage** - prompt sent as-is

---

### 2. **Backend Route Handler** (`app/routes/generation.py` - `generate()`)
```python
# Lines 53-56: Extract prompt from request
prompt = data.get('prompt', '').strip()
style = data.get('style', '').strip().lower()
color_1 = data.get('color_1', '').strip() or None
color_2 = data.get('color_2', '').strip() or None
```

✅ **Only validation happens here**:
- Strip whitespace
- Validate prompt length (min 3 chars)
- Validate style is in supported list
- No prompt content modification

```
Prompt after routing: "a beautiful floral design" (unchanged)
```

---

### 3. **Background Processing** (`app/routes/generation.py` - `_process_generation()`)
```python
# Line 260: Calls generator.generate() with original prompt
image, actual_seed = generator_instance.generate(
    prompt=prompt,  # "a beautiful floral design"
    style=style,    # "bandhani"
    color_1=color_1,  # "blue"
    color_2=color_2,  # "white"
    seed=seed
)
```

✅ **Prompt still unchanged** at this point

---

### 4. **Model Generation** (`app/utils/generator.py` - `generate()` method)

#### **Line 260: PROMPT ENHANCEMENT HAPPENS HERE**
```python
# Build enhanced prompt
full_prompt = self._build_prompt(prompt, style, color_1, color_2)
negative_prompt = self._get_negative_prompt()
```

#### **The `_build_prompt()` Transformation** (Lines 418-445)

**Original prompt:**
```
"a beautiful floral design"
```

**Gets transformed to:**
```
"a beautiful floral design, traditional tie-dye bandhani pattern, intricate circular motifs, symmetrical design, seamless pattern, tileable, primary color blue, secondary color white, high quality, detailed, professional, textile design"
```

**What was added:**
1. ✏️ **Style description** (based on selected style):
   - bandhani: "traditional tie-dye bandhani pattern, intricate circular motifs, symmetrical design"
   - ikat: "resist-dyed ikat textile, abstract geometric patterns, blurred edges"
   - block_print: "hand-stamped block print pattern, repetitive motifs, artisanal texture"
   - paisley: "classic paisley pattern, ornate teardrop shapes, flowing design"

2. ✏️ **Seamless pattern instructions**: "seamless pattern, tileable"

3. ✏️ **Color information** (if provided):
   - "primary color blue"
   - "secondary color white"

4. ✏️ **Quality prompts**: "high quality, detailed, professional, textile design"

#### **Negative Prompt** (Lines 447-452)
Also added automatically:
```
"ugly, distorted, blurry, low quality, watermark, text, human, face, people, figure, bad proportions, deformed, asymmetrical, irregular, noise"
```

---

### 5. **Text Encoding** (Lines 263-300)
```python
# The ENHANCED prompt is what gets tokenized and encoded:
text_inputs = self.tokenizer(
    full_prompt,  # ← This is the enhanced prompt!
    padding="max_length",
    max_length=self.tokenizer.model_max_length,
    truncation=True,
    return_tensors="pt"
)
```

✅ **The enhanced prompt is converted to embeddings and sent to the model**

---

### 6. **Model Inference** (Lines 310-340)
The enhanced prompt embeddings are used in the UNet denoising loop:
```python
# Line 329: Encoder receives the enhanced prompt embeddings
encoder_hidden_states = torch.cat([neg_embeds, prompt_embeds])
noise_pred = self.unet(
    latent_model_input,
    t,
    encoder_hidden_states=encoder_hidden_states,  # ← Enhanced prompt here!
    added_cond_kwargs=added_cond_kwargs,
    return_dict=False
)
```

---

## Prompt Modification Summary

| Stage | Original Prompt | Modified Prompt | File | Lines |
|-------|-----------------|-----------------|------|-------|
| Frontend | `"a beautiful floral design"` | Same | `api.ts` | 53-54 |
| Route Handler | `"a beautiful floral design"` | Same (validation only) | `generation.py` | 53-56 |
| Background Thread | `"a beautiful floral design"` | Same | `generation.py` | 260 |
| **Generator** | `"a beautiful floral design"` | **ENHANCED** ✏️ | `generator.py` | 260, 418-445 |
| Model Input | N/A | **Enhanced version** | `generator.py` | 263-300 |

---

## Example Transformations

### Example 1: Bandhani Style with Colors
**Frontend Input:**
```json
{
  "prompt": "colorful geometric shapes",
  "style": "bandhani",
  "color_1": "red",
  "color_2": "gold"
}
```

**What Model Receives:**
```
colorful geometric shapes, traditional tie-dye bandhani pattern, intricate circular motifs, symmetrical design, seamless pattern, tileable, primary color red, secondary color gold, high quality, detailed, professional, textile design
```

### Example 2: Block Print with Single Color
**Frontend Input:**
```json
{
  "prompt": "traditional floral",
  "style": "block_print",
  "color_1": "indigo"
}
```

**What Model Receives:**
```
traditional floral, hand-stamped block print pattern, repetitive motifs, artisanal texture, seamless pattern, tileable, primary color indigo, high quality, detailed, professional, textile design
```

### Example 3: No Colors
**Frontend Input:**
```json
{
  "prompt": "abstract patterns",
  "style": "ikat"
}
```

**What Model Receives:**
```
abstract patterns, resist-dyed ikat textile, abstract geometric patterns, blurred edges, seamless pattern, tileable, high quality, detailed, professional, textile design
```

---

## Why Prompt is Modified

The modifications ensure:
1. **Style Consistency**: Style description helps model understand desired pattern type
2. **Seamless Generation**: "seamless pattern, tileable" ensures the output can be tiled
3. **Color Accuracy**: Color specifications guide the model's color selection
4. **Quality Control**: "high quality, detailed, professional" improves output quality
5. **Negative Guidance**: Negative prompt prevents unwanted features

---

## Key Code References

| File | Method | Purpose | Lines |
|------|--------|---------|-------|
| [api.ts](../textile_generator_frontend/src/services/api.ts) | `startGeneration()` | Sends prompt to backend | 53-54 |
| [generation.py](../textile_generator_backend/app/routes/generation.py) | `generate()` | Route handler, validates prompt | 53-56 |
| [generation.py](../textile_generator_backend/app/routes/generation.py) | `_process_generation()` | Background task, calls generator | 260 |
| [generator.py](../textile_generator_backend/app/utils/generator.py) | `generate()` | **Enhances prompt** | 260 |
| [generator.py](../textile_generator_backend/app/utils/generator.py) | `_build_prompt()` | **Performs enhancement** | 418-445 |
| [generator.py](../textile_generator_backend/app/utils/generator.py) | `_get_negative_prompt()` | Adds negative prompt | 447-452 |

---

## Conclusion

✅ **The prompt IS modified**, but **only in the generator before tokenization** (stage 4)
- **Stages 1-3**: Prompt passes through unchanged (only validation)
- **Stage 4**: Prompt is enhanced with style, color, and quality keywords
- **Stage 5+**: Enhanced prompt is what reaches the model

This enhancement is intentional and improves generation quality.
