# 고정 그림체 문구

그림을 만들 때 프롬프트는 이 파일의 문구를 **그대로 복사해** 조합한다. 문구를 바꿀 때는 이 파일만 고친다.
(CLAUDE.md, imagegen, instatoon은 모두 이 파일을 참조한다.)

## 조합 순서
1. 기준 이미지 설명 (기준 이미지를 넣을 때만)
2. 장면 설명 (컷마다 새로 씀)
3. 등장 인물 문구 (등장하는 인물만)
4. 그림체 문구
5. 구도·말풍선 자리 문구
6. 금지 문구

---

## 1. 기준 이미지 설명
기준 이미지: `references/charsheet_hangyeol.png` + `references/charsheet_bookmark.png`를 합친 이미지(왼쪽 한결, 오른쪽 책갈피).

```
Keep the exact same character design and drawing style as the reference image. The reference is a character sheet: left = Hangyeol, right = Bookmark the cat. Do NOT copy the sheet layout. Draw ONE single full-bleed webtoon panel.
```

## 3. 등장 인물

### 한결
```
Hangyeol, a 32-year-old Korean office worker, shoulder-length DARK espresso-brown bob hair, THICK BOLD round black horn-rimmed glasses, beige knit sweater, navy pants, brown canvas tote bag with books sticking out
```
표정은 캐릭터 시트에 있는 것만 쓴다.

| 표정 | 문구 |
|---|---|
| 미소 | `gentle closed-mouth smile` |
| 웃음 | `laughing with eyes squeezed shut and mouth wide open` |
| 놀람 | `surprised, eyes wide and round, small open mouth` |
| 생각 | `thinking, eyes looking up to the side, one finger on the chin` |
| 신남 | `excited, sparkling eyes, big open smile, both fists raised` |
| 졸림 | `sleepy, droopy half-closed eyes behind the glasses, yawning` |

### 책갈피 (고양이)
```
Bookmark, a small gray striped tabby cat with a round face, white chest and white paws, simple cute style
```

| 표정 | 문구 |
|---|---|
| 졸림 | `sleeping with eyes closed, a small light-blue snot bubble at the nose` |
| 뚱함 | `grumpy, flat half-lidded eyes, frowning mouth` |
| 호기심 | `curious, head tilted, big round eyes looking up` |
| 기쁨 | `happy, eyes closed in smiling arcs, open smiling mouth` |
| 놀람 | `surprised, very wide eyes, ears straight up, fur puffed` |

## 4. 그림체
```
Simple Korean webtoon style, soft pastel colors, clean thin lines, flat shading, warm cozy atmosphere, simple uncluttered background.
```

## 5. 구도·말풍선 자리
생성은 `1024x1536`(2:3)이고, 4:5로 자르면 **위아래 약 8%씩 잘린다.** 그래서 말풍선 자리는 잘리는 부분을 더해서 비운다.

| 최종 그림(4:5)에서 비울 영역 | 생성 프롬프트에 쓸 값 |
|---|---|
| 위 20% | upper 25% |
| 위 25% | upper 30% |
| 위 30% | upper 33% |
| 아래 20~30% | 위와 같은 값을 lower로 |

```
Keep the characters' faces and key objects in the middle of the frame. Leave the {upper|lower} {N}% of the image as plain empty background for speech bubbles, with nothing important there.
```
말풍선 자리가 위와 아래 둘 다 필요하면 두 문장을 모두 넣고, 인물은 세로 가운데 40%에 둔다.

## 6. 금지
```
No text, no letters, no numbers, no symbols, no question marks, no exclamation marks, no X marks, no speech bubbles, no panel border frame, no writing on book covers, spines or pages.
```
