# /pre-pr — PR 전 체크리스트

PR을 올리기 전에 아래 항목을 순서대로 실행하고 결과를 리포트한다.

## 실행 순서

1. **변경 내용 분석**
   ```bash
   git diff main...HEAD
   ```
   - 누락된 테스트가 없는지 확인
   - 하드코딩된 값(비밀키, 로컬 경로 등) 없는지 확인
   - 컨벤션 위반(Conventional Commits, 네이밍) 없는지 확인

2. **프론트엔드 타입 체크**
   ```bash
   cd frontend && npm run type-check
   ```

3. **프론트엔드 린트**
   ```bash
   cd frontend && npm run lint
   ```

4. **백엔드 테스트** (테스트 파일이 있는 경우)
   ```bash
   cd backend && python -m pytest
   ```

5. **코드 리뷰**
   - `/code-review` 실행 후 지적된 사항 반영

6. **PR 설명 초안 작성**
   - **Why**: 왜 이 변경이 필요한가
   - **What**: 무엇을 변경했는가
   - **테스트 방법**: 어떻게 검증했는가

## 리포트 형식

각 단계 결과를 ✅ / ❌ 로 표시하고, 실패 항목은 수정 후 재실행한다.
