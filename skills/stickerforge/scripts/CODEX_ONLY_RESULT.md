# Codex 단독 경로 실측 (2026-11-06)

## 결과

바깥 `codex exec --dangerously-bypass-approvals-and-sandbox` 안에서 `setsid nohup python3 scripts/run.py <작업폴더> --yes > runner.log 2>&1 < /dev/null &` 로 러너를 분리 실행하고, 바깥이 20초마다 runner.log 를 확인하는 방식으로 3장 완주했다. 바깥 모델은 gpt-6.1-terra low, 안쪽 생성은 gpt-6.1-terra medium. 바깥 턴 3분 18초, 납품 3장(export/ 에 PNG 3개와 DELIVERY.md).

## 성립 조건

- 바깥이 러너를 띄운 뒤 턴을 끝내지 않고 상태를 확인하며 기다려야 한다. 11-06 앞선 시험에서 바깥 턴이 10초 만에 끝났을 때는 안쪽 스레드가 이미지 없이 사라졌다. 이번 시험에서 setsid 분리 자체의 효과(턴이 끝난 뒤 러너 생존)는 따로 확인하지 못했다. 바깥이 끝까지 대기했기 때문이다.
- 바깥은 전체 권한이어야 한다. 일반 권한이면 안쪽 codex 가 Read-only 로 실패한다.
- 러너가 승인 대기(exit 3)에서 서는 것을 막으려고 `--yes` 를 썼다. 사람 확인 A, B, C 를 지키려면 바깥이 run.py 가 멈춘 지점에서 사람에게 묻고 `--approve` 로 이어 실행한다.
- 상태는 runner.log 와 `run.py <작업폴더> --status`(manifest.jsonl)로 읽는다.

## 대안: 내장 도구 순차 호출 모드

분리 실행이 안 되는 환경(바깥 턴이 짧게 끝나는 경우, 샌드박스)용. 바깥 에이전트 자신이 내장 image_gen 을 장마다 한 번씩 호출한다. 병렬은 없다.

    python3 run.py <작업폴더> --next                                      프롬프트, 참조, transparent_background 값을 JSON 으로
    (바깥이 그 프롬프트를 그대로 image_gen 에 넣고 참조 이미지를 붙여 생성)
    python3 run.py <작업폴더> --ingest <id> --file <생성된 PNG> [--thread-id T]
    ... --next 가 done:true 를 낼 때까지 반복
    python3 run.py <작업폴더> --from S4 --yes                              게이트, 재시도 대상 확인, 시트, 납품

구현과 등록 동작(--next, --ingest, 원장 기록, 알파 정리)은 가짜 PNG 로 시험했다. 이 모드에서 바깥이 실제로 장마다 image_gen 을 부르는 전체 시나리오는 이번에 돌리지 않았다. S5 재시도는 provider 생성 경로를 쓰므로 이 모드에서는 불합격 id 를 다시 `--next` 로 받으려면 해당 out 파일이 없어야 한다(불합격 파일은 qc/rejected 로 옮겨진다).

## 한계

- 한도는 계정 단위라 동시성을 올려도 처리량이 늘지 않는다.
- 첫 장 시험 생성 약 80-170초, 이후 2장 동시 약 90초.
