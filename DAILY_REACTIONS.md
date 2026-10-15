# 지정 영상 일일 신규 반응 분석

매일 기존 수치 수집에 이어 **댓글·채팅 확보 → 중복 제거 → 한국어 분석 → 저장 검증 → GitHub 커밋 → 공개 배포 확인**까지 수행합니다. 범위는 `data/targets.json`의 10개 영상만입니다. 다른 영상이나 채널 전체를 검색하지 않습니다.

## 읽기와 공개 수집

1. Sites get_site로 현재 비공개 서비스 접근을 얻고 `/api/runbook`, `/api/data`, `/api/reactions`를 읽습니다. 인증은 이 Site에만 보내고 메모리/숨김 stdin에서 다룹니다. 공개 GitHub 파일·명령·출력에 인증을 넣지 않습니다.
2. GitHub main의 이 문서, `scripts/collect-reactions.py`, `scripts/prepare-reactions.mjs`, `data/targets.json`, 두 공개 JSON과 각각의 현재 SHA를 읽습니다. 수집 스크립트는 저장소에서 실행합니다. 현재 수치와 private reaction state를 임시 파일로 준비하고 다음을 실행합니다.

   `python scripts/collect-reactions.py --metrics metrics.json --state private-reactions.json --output reaction-candidates.json`

   스크립트는 공개 접근만 사용하며 유료 도구를 호출하지 않습니다. 결과의 `candidates`는 분석을 위한 임시 원문이므로 커밋하지 않습니다. 기존 `seen` 해시로 중복을 제거합니다. 동일 문구라도 서로 다른 메시지 ID이면 독립 메시지로 남깁니다. 수집 범위를 넘는 채널/다른 영상은 조회하지 않습니다.
3. 일반 댓글은 최신순 최대 100개 스레드까지 확인합니다. 카운트가 그대로여도 0보다 크면 매일 원문을 확인합니다. 일부 페이지·답글만 확보한 경우 `partial`로 표시하고 전체 조사로 표현하지 않습니다. 오늘 실제 관측한 댓글 수가 0이면 `count_zero`, 실패·접근 제한은 `unavailable`입니다. 성공적으로 확인된 결과에 새 항목이 없을 때만 신규 확보 0건이라고 말합니다.
4. 종료 방송에서 완전히 확보한 채팅은 `archived`로 유지하고 다시 합산하지 않습니다. 아직 확보되지 않은 지정 영상의 채팅은 다시보기를 확인하되 이전 방송의 추가 확보분은 `backfill`입니다. 신규 영상이 추가되었다고 기존 방송 채팅을 오늘 작성된 반응으로 표시하지 않습니다. 현재 실행에서 확보된 원문만 사용하며 과거 조회수 재조회는 하지 않습니다.
5. Facebook 공개 페이지의 조회·반응 숫자로 댓글 내용을 추정하지 않습니다. 기본 공개 수집기는 Facebook 댓글·채팅 원문을 추출하지 못하므로 `unavailable`을 남깁니다. 별도 접근 가능한 공개 원문이 실제 확인될 때만 해당 영상 ID와 연결해 분석하고 상태를 갱신합니다. 로그인 장벽이나 접근 제한을 우회하지 않습니다.

## 필요한 경우에만 유료 댓글 보완

공개 경로가 실패했고 해당 YouTube 영상의 댓글 수가 0보다 크거나 미확인이면 vidIQ `video_comments(videoId, order:"time", maxResult:100)` 한 페이지를 사용할 수 있습니다. 현재 도구 비용은 5크레딧이며 실행 때 다시 확인합니다. 영상별 KST 하루 1회까지만 허용하고 같은 페이지를 재호출하지 않습니다. 완료된 check가 이미 있으면 같은 날 유료 보완을 반복하지 않습니다. 과거 통계·채널 전체 조회·다른 영상 검색은 금지합니다.

비용은 **기존 동일 총 승인 한도**에 합산합니다. `/api/data`의 `budgetCap/creditsSpent/creditsRemaining`과 vidIQ balance를 확인합니다. 호출 직전 `/api/config`에 `lastReactionBillableKey: "날짜:영상ID"`, `lastReactionBillableState:"pending"`을 저장합니다. pending 완료가 불확실하면 재호출하지 않습니다. `_credits.used` 확인 후 공유 예산을 갱신하고 completed로 기록합니다. 수치 수집용 `lastBillableDay/State`와 구분합니다. 가격 미확인·예산 부족이면 유료 수집을 멈추고 실패 상태와 비용 제약을 알립니다. 추가 유료 보완으로 가능한 남은 수집 횟수가 줄어들 수 있습니다.

## 원문 분석

- `candidates`의 태국어 맥락을 읽고 **한국어 의역**을 작성합니다. 댓글에서 추정한 사실을 검증된 사실로 쓰지 않습니다. 질문·풍자·짧은 호응·친목을 기계적으로 긍정/부정으로 세지 않습니다.
- `sentiment`: positive / negative / neutral / mixed / uncertain / other. `direction`은 긍정, 참여 의향, 질문, 공략, 문제 제보, 방송 품질, 판단 유보 등 구체적인 분류를 사용합니다.
- 실제 게임 성능과 스트리밍 품질 불만을 구분합니다. 원어민 독립 검수가 없다는 한계를 유지합니다.
- 작성자의 채널 ID를 해당 영상의 확인된 소유 채널 ID와 비교한 후 방송자를 제외합니다. 확인 불가능한 경우 `authorRole:unverified`로 따로 표기하고 시청자 확인 표본 비율에서 제외합니다. 작성자 이름·ID·핸들·연락처·전체 원문은 공개하지 않습니다.
- 채팅은 비방송자·비링크·비어 있지 않은 새 확보 메시지 중 방송 순서상 균등 간격 최대 40건입니다. 일반 댓글은 확보된 최대 100개 스레드의 실제 새 항목을 분석합니다. 반복 스레드나 같은 작성자를 독립 영상 지지 수로 세지 않습니다.
- `collectedAt`과 실제 `publishedAt`을 구분합니다. 상대 작성일을 정확한 시간으로 환산하지 않습니다. 정확한 작성 시각이 직전 확인 이후임을 입증할 때만 `newly_published`, 그 외 새로 찾은 댓글은 `first_observed`, 종료 방송 채팅은 `backfill`입니다.
- 각 item에는 `key,videoId,kind,collectedAt,publishedAt,novelty,sentiment,direction,summary_ko,note,url,authorRole,sample`을 넣습니다. source URL은 해당 영상 또는 댓글·방송 시점이어야 합니다. kind는 comment/reply/chat입니다. `key`는 SHA-256(`kind|videoId|원본메시지ID`)입니다.
- 체크에는 `key,videoId,kind,day,checkedAt,status,fetched,firstObserved,analyzed,excluded,hasMore,method,note`를 넣습니다. status는 complete/partial/unavailable/count_zero/archived. `analyzed`를 실제 저장 item 수로 갱신하고, 확보 수·분석 수·제외 수·미확인 범위를 모두 보존합니다. `key`는 SHA-256(`check|videoId|kind|checkedAt`)입니다.

## 저장·배포

1. `/api/reactions`에 `{items,checks,seen}`을 POST합니다. 한 요청 최대 items 300/checks 100/seen 3000입니다. 큰 경우 여러 요청으로 나누되 동일 키·시각을 유지합니다. 저장 실패 시 같은 데이터만 재전송하고 원문이나 유료 도구를 다시 조회하지 않습니다. 서버는 키로 중복을 방지하고 기존 이력을 보존합니다.
2. GET `/api/reactions`로 재확인하고 `/api/config`의 `lastReactionAt/lastReactionStatus`를 실제 결과로 갱신합니다. 기존 1,844건 채팅·258건 표본·79건 근거는 별도 baseline으로 보존합니다.
3. 전체 검증된 reaction export를 `scripts/prepare-reactions.mjs`에 전달해 `docs/data/reactions.json`을 만듭니다. 공개 파일에는 `schemaVersion,publishedAt,baseline,items,checks`만 포함합니다. private `seen`, 임시 원문, 인증, 예산을 포함하지 않습니다.
4. 기존 `COLLECTOR_SYNC.md`에 따라 수치 파일도 갱신합니다. 두 JSON의 현재 SHA를 조건으로 커밋합니다. 기존 기록을 덮어 지우지 않고 필요 시 최신 파일을 다시 읽어 병합합니다. 갱신 후 GitHub 파일과 공개 Pages 데이터 URL을 다시 읽어 실제 수치·분석 건수·시각을 검증합니다. 커밋만 성공한 상태를 배포 완료라고 알리지 않습니다.
5. 일일 보고에는 현재 수치·전일 변화, 신규 확보/실제 분석 수, 대표 긍정·부정·질문, 미확보 영상과 이유, 추가 비용·잔여 예산, GitHub/공개 배포 결과를 짧게 알립니다. 비어 있는 표본을 분석 완료로 보고하지 않습니다.
