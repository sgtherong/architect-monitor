# 기존 일일 수집 작업의 GitHub 동기화

기존 일일 수집 작업이 저장 자료를 공개 대시보드에 동기화할 때 따르는 절차입니다.

## 연결값

- GitHub 소유자: `sgtherong`
- 저장소: `sgtherong/architect-monitor`
- 대상 파일: `docs/data/observations.json`
- 대상 브랜치: `main`

## 절차

1. `DAILY_REACTIONS.md`의 무료 공식 API 절차를 수행하고 원본 Site 저장 결과를 다시 읽습니다. `POST /api/youtube/metrics`는 같은 KST 날짜의 공식 API 수치가 이미 있으면 재조회하지 않습니다. GitHub 동기화를 위해 수집을 반복하거나 과거 통계를 조회하지 않습니다. vidIQ 유료 수치·댓글 보완은 비활성화합니다.
2. 지정 10개 영상의 전체 관측 기록을 보존합니다. `observedAt`, 한국 시간 `day`, `null`, `precision`, `status`, `source`, `note`를 바꾸지 않습니다. 다른 영상이나 채널 전체 지표는 추가하지 않습니다.
3. 공개 JSON에는 `schemaVersion: 1`, `publishedAt`, `rows`, `stored: true`, `config.scheduleStatus`, `config.historyStatus`만 포함합니다. `rows`의 필드는 `scripts/prepare-snapshot.mjs`의 허용 목록을 따릅니다. 접근 토큰, 예산·잔액, 수집 내부 식별자는 포함하지 않습니다.
4. GitHub의 현재 파일과 SHA를 읽습니다. `publishedAt`을 제외한 데이터가 동일하면 커밋하지 않습니다. 변경이 있을 때 현재 SHA를 조건으로 파일 하나만 갱신합니다. 충돌 시 최신 파일을 다시 읽고 누락된 관측이 없는지 확인하며 기존 기록을 덮어 지우지 않습니다.
5. 업로드한 파일을 다시 읽어 10개 영상의 기록·관측 시각·미확인 값이 일치하는지 확인합니다. 결과에는 GitHub 반영 성공 여부와 수집 실패를 구분합니다.
6. GitHub 권한·Pages 오류가 나면 오류를 알리고 기존 서버의 저장 자료와 수집 작업은 유지합니다. 동일 수집을 유료로 재실행하지 않습니다.

GitHub Pages 반영은 GitHub의 배포 처리 이후 이루어집니다. 새 공개 링크는 실제 Pages 설정 화면이나 배포 결과에서 확인한 주소를 사용합니다.

2026-10-15 추가: JJAMx Gaming & Cosplay의 Facebook 영상 `1443913631040943`, PuddingKat CH의 YouTube 영상 `G36iQinLR0I`. 두 영상의 이전 날짜 수치는 소급 수집하지 않으며, 기존 채팅·감성 분석에 포함된 것으로 표시하지 않습니다.

## 일일 신규 반응 분석 추가

2026-10-15 사용자 요청에 따라 매일 `DAILY_REACTIONS.md`의 댓글·채팅 수집 및 분석을 수치 수집과 함께 수행합니다. `docs/data/reactions.json`도 별도로 동기화합니다. 수치 파일은 기존 형식을 유지하고 원문·seen 해시·예산은 공개하지 않습니다. 기존 고정 표본은 그대로 보존하며 매일 수집된 근거와 분리합니다.
