# gates 규약

run.py 는 S4 에서 `scripts/gates/*.py` 를 파일명 순서로 순회 호출한다. `_` 로 시작하는 파일은 건너뛴다.

## 호출

    python3 gates/<name>.py <projectDir>/out [게이트별 옵션]

폴더 하나를 받아 안의 PNG 를 모두 검사한다. 중복 검사처럼 세트 전체를 봐야 하는 게이트도 같은 호출 방식이다.
run.py 는 폴더의 결과 중 이번에 검사할 id 의 행만 읽는다.

게이트별 옵션은 spec.json 의 `gates` 에 게이트 이름(파일명에서 `gNN_` 뺀 것)으로 적는다.
`min_px` 는 size 게이트의 `--min-px` 로 전달된다.

    "gates": { "margin": ["--margin", "20"], "dup": ["--max-dist", "10"] }

## 출력

stdout 마지막 줄에 JSON 한 개. 다른 출력은 stderr 로.

    {"gate": "alpha", "results": [{"file": "t001.png", "pass": true, "code": "OK", "detail": ""}]}

file 에서 확장자를 뺀 것이 컨셉 id 이다. 불합격 행은 code(짧은 사유 코드)와 detail(사람이 읽는 설명)을 낸다.

## exit code

| 코드 | 뜻 |
|---|---|
| 0 | 모든 파일 통과 |
| 1 | 하나 이상 불합격. S5 에서 해당 id 만 재생성 |
| 그 외 | 게이트 자체 오류. run.py 가 불합격으로 세지 않고 exit 7 로 멈춘다 |

## 규칙

- 표준 라이브러리 + Pillow + numpy 만 쓴다. 이미지를 고치지 않는다(읽기 전용).
- spec.json 의 `transparent` 가 false 이면 이름에 alpha, checker, margin, outline 이 들어간 게이트는 호출하지 않는다.
- 게이트가 하나도 없으면 run.py 는 경고를 기록하고 최소 검사(열림, 최소 크기, 투명 요구 시 알파 존재와 투명 영역 비율)만 한다.
