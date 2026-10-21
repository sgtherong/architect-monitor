# 지정 영상 일일 신규 반응 분석

매일 기존 수치 수집에 이어 **댓글·채팅 확보 → 중복 제거 → 한국어 분석 → 저장 검증 → GitHub 커밋 → 공개 배포 확인**까지 수행합니다. 범위는 `data/targets.json`의 10개 영상만입니다. 다른 영상이나 채널 전체를 검색하지 않습니다.

## 무료 공식 API 수집 (2026-10-21 전환)

1. Sites get_site로 현재 서비스 접근을 얻고 `/api/runbook`, `/api/data`, `/api/reactions`를 먼저 읽습니다. 이 Site는 owner-private이며 인증은 해당 Site에만 전송합니다.
2. `POST /api/youtube/metrics`에 빈 JSON `{}`를 보내 고정 YouTube 8개의 현재 수치를 한 번에 수집합니다. 서버의 `YOUTUBE_API_KEY` secret만 사용합니다. 성공한 공식 API 수치는 KST 날짜별로 캐시되어 재호출 시 `cached:true, quotaUnits:0`입니다. 409는 진행 중 또는 저장 확인 필요 상태이므로 원본 자료를 확인합니다. `GET /api/data`로 저장 결과를 검증합니다. 전환 당일의 기존 vidIQ 관측과 새 공식 관측은 모두 보존합니다.
3. `POST /api/youtube/reactions`에 `{}`를 보냅니다. 댓글 수가 0보다 크거나 미확인이면 최신순 최대 100개 스레드와 반환된 답글을 읽습니다. 댓글 수가 같아도 확인합니다. 응답의 `candidates`는 저자 식별 정보가 제거된 **임시 분석 입력**이며 원문은 서버에 저장하지 않습니다. `checks`, `seen`, `reusedChecks`가 함께 반환됩니다. 성공한 공식 API 체크가 오늘 이미 저장됐으면 재조회하지 않습니다.
4. 응답을 임시 `official-comments.json`으로 준비하고 다음 공개 보완 수집기를 실행합니다. 파일과 원문은 GitHub·공개 아티팩트에 올리지 않습니다.

   `python scripts/collect-reactions.py --metrics metrics.json --state private-reactions.json --official-comments official-comments.json --output reaction-candidates.json`

   `--official-comments`가 있으면 YouTube 일반 댓글을 다시 스크래핑하지 않습니다. 종료 방송의 완전 확보 채팅은 `archived`로 유지하고, 미확보 지정 방송만 다시보기를 확인합니다. Facebook 2개는 공개 경로를 확인하되 원문을 검증하여 추출하지 못하면 `unavailable`입니다. 공개 수치로 반응 내용을 추정하지 않습니다.
5. `candidates`만 분석하여 저장할 items를 만듭니다. 체크의 `analyzed`는 실제 저장되는 해당 영상·종류의 item 수로 갱신합니다. 실패·불완전 수집을 신규 0건으로 표현하지 않습니다. 종료 방송 채팅 추가분은 `backfill`입니다. 기존 seen과 중복인 항목은 재분석하지 않습니다.

## 비용과 실패 처리

**vidIQ 및 다른 유료 API는 수치·댓글 모두 사용하지 않습니다.** 무료 경로 실패 시 자동으로 유료 경로를 호출하지 않습니다. 기존 누적 사용액과 잔여 크레딧은 역사적 기록으로 그대로 보존합니다. Google API quotaUnits는 vidIQ 크레딧과 다른 수치입니다. 키 미설정·API 제한·할당량 부족·네트워크 실패는 실제 오류로 알리고 기존 기록을 유지합니다. 임시 429 등으로 기존 일정을 삭제하지 않습니다.

GitHub `YOUTUBE_API_KEY`는 연결 검증용이며, 동일 키가 연결된 비공개 Site의 production secret에도 설정되어 있습니다. 주기적 수집은 기존 자동 작업 하나가 Site의 무료 엔드포인트를 호출합니다. 키 교체 시 양쪽 비밀 설정을 갱신해야 합니다. 키 값은 소스·문서·명령행·로그·공개 JSON에 넣지 않습니다.

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
