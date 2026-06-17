# nurse_jxl（双变体）

预设含两个动作变体，`_1` 默认三分侧面，`_2` 正面微俯。使用时拼合：
**完整 prompt = `common prompt prefix` + 对应变体后缀**

22岁护理专业毕业生，四川面孔，梨形身材成女，162cm/51kg/B罩杯，学生气，黑发全卷起大夹子夹住，护士白上衣+白裤子+护士帽+白鞋，自然神情

## common

### negative
nsfw, lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry, ugly, deformed, thick painting, heavy shadows, dark, muted colors, oversaturated, loli, child, young girl, teenage, soft focus, haze, fog, muscular, fat, large breasts, holding flowers, bouquet, smiling, fake smile, forced expression, exaggerated expression, 3d render, 3d model, cgi

### params
--jxl --portrait --steps 40 --cfg 7

### 4k
--jxl --steps 30 --cfg 7 --seed <SEED> --4k

### 16:9 横版
--jxl --steps 40 --cfg 7 --seed <SEED>
（去掉 `--portrait`，加 `wide angle shot, wide field of view` 到 prompt）

---

### common prompt prefix
masterpiece, best quality, ultra detailed, 1woman, adult female, 22 years old, recent nursing graduate, white nurse top, white nurse pants, white shoes, black hair, all hair rolled up in a bun secured with a large hair clip, fair skin, delicate pale skin, student-like atmosphere, innocent look, pear-shaped body, 162cm height, 51kg, b cup, sichuan chinese face features, full body, head to toe, standing, calm expression, soft gaze, gentle eyes, subtle expression, by bright window, hospital ward, well-balanced composition, sharp focus, crisp linework, highly detailed shading, detailed hair strands with highlights, clear eyes with sparkling reflections, fine fabric texture, soft white color palette, warm sunlight illumination, beautiful cloth folds, elegant, refined, high quality anime illustration

## _1（三分侧面，双手搭小腹，视线微侧）
hands resting on lower abdomen, nurse cap, three-quarter view

## _2（正面微俯，视线向前，小帽别于发髻）
hands resting on lower abdomen, small nurse cap pinned on top of hair bun, facing viewer, looking at viewer, front view, slightly high angle, looking slightly downward

---

> 使用：`common prompt prefix` + 对应变体的后缀即可组成完整 prompt。
