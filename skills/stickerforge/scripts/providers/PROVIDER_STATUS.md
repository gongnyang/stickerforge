# provider 상태

2026-11-06 기준. README 의 지원 표에 옮길 근거.

| provider | 구현 | 실제 호출 시험 | 투명 배경 | 크기 |
|---|---|---|---|---|
| codex | providers/codex.py | 완료. 3장 완주(gpt-6.1-terra medium) | 내장 도구의 transparent_background=true. 알파 채널이 실제로 나옴(1254x1254 RGBA, 투명 영역 약 62%) | 인자 없음. 1254px 근처 결과. 300dpi 로 10.6cm. 업스케일 안 함 |
| openai | providers/openai.py | 불가. 이 PC에 OPENAI_API_KEY 없음. 문서 기준 구현, 미시험 | gpt-image-2 는 background=transparent 미지원이라 초록 단색 배경 + 크로마키. gpt-image-1.5 는 spec 에서 model 을 직접 지정할 때만 네이티브 투명. 모델을 몰래 바꾸지 않음 | size 인자 지원(spec.openai.size) |
| gemini | providers/gemini.py | 불가. 이 PC에 GEMINI_API_KEY 없음. 문서 기준 구현, 미시험 | 미지원이라 초록 단색 배경 + 크로마키 | 모델 기본값 |

## 시험하지 못한 것

- openai, gemini 의 실제 응답 형식과 오류 코드. 응답 파싱은 공식 문서의 필드(data[0].b64_json, candidates[0].content.parts[].inlineData.data)를 따랐다.
- 크로마키 품질. postprocess.chroma_key 는 합성 이미지로만 확인 가능하고 실제 생성물로는 못 봤다. 결과는 S4 게이트(알파, 체크무늬, 테두리)가 잡는다.
- 키가 있어도 openai 는 조직 인증이 필요할 수 있다. 401, 403, 429 는 재시도 없이 멈추고(exit 6) 재개 명령을 안내한다.

## 선택 규칙

doctor.py 가 codex, openai, gemini 순으로 쓸 수 있는 첫 경로를 고른다. spec.provider 로 지정했는데 쓸 수 없으면 다른 경로로 바꾸지 않고 사유와 함께 exit 2 로 끝낸다.
