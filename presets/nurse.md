# nurse

成年女护士窗边捧花，清爽粉白淡雅圣洁风

## prompt
masterpiece, best quality, ultra detailed, 1woman, adult female nurse, pure white nurse uniform with intricate fabric folds and lace details, holding fresh bouquet of pink roses and white lilies in hands, standing by bright window, three-quarter view, well-balanced composition, sharp focus, crisp linework, highly detailed shading, detailed hair strands with highlights, clear eyes with sparkling reflections, fine fabric texture, detailed flower petals with dew drops, soft pink and white color palette, warm sunlight illumination, beautiful cloth folds, elegant, refined, high quality anime illustration

## negative
nsfw, lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry, ugly, deformed, thick painting, heavy shadows, dark, muted colors, oversaturated, loli, child, young girl, teenage, soft focus, haze, fog

## params
--steps 40 --cfg 7

## 4k
--steps 30 --cfg 7 --seed <SEED> --4k

---

## 2. 粉发护士花嫁（萝莉体型）

```powershell
& "E:\sd-comfyui\python\python.exe" "E:\sd-comfyui\comfyui_bridge.py" `
  --prompt "masterpiece, best quality, 8k, ultra detailed, anime girl, long pastel pink gradient hair, flowing hair, pink amethyst eyes, gentle soft smile, delicate facial features, tiny nurse cap decorated with cherry blossoms, white pink gradient long nurse wedding dress, pink lace embroidery all over skirt, high neck long sleeve, wedding nurse hybrid outfit, holding big bouquet of pink roses, green leaves, european gothic church corridor, tall stained glass windows, soft backlight, wisteria pink cherry blossom vines hanging everywhere, floating pink petals, vintage carved window frame, soft pastel pink purple color palette, watercolor texture, hazy dreamy atmosphere, soft rim light, shallow depth of field, delicate brush strokes, ethereal glow, healing aesthetic" `
  --negative "lowres, bad anatomy, bad hands, missing fingers, extra limbs, ugly, blurry, deformed, dark tone, dull color, rough sketch, messy line, male, boy, multiple people, harsh shadow, black background, sharp color, gore, dirty texture, adult, mature, big breasts, large body, tall" `
  --lora "Genshin_Nahida_AP_v1.safetensors" --lora-strength 0.9 --steps 40 --cfg 7 --seed -1 --batch-size 10
```
