import time
import sys
import io
import os
import subprocess
from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8', write_through=True)
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8', write_through=True)

def main():
    print("Playwright를 시작합니다 (Headed 모드)...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        print("GitHub 로그인 페이지로 이동합니다. 브라우저 창에서 로그인을 끝내주세요!")
        page.goto("https://github.com/login")
        
        # 사용자가 로그인을 완료할 때까지 최대 300초 대기
        login_success = False
        for i in range(300):
            current_url = page.url
            if "github.com/login" not in current_url and "github.com/session" not in current_url:
                if "github.com" in current_url:
                    print(f"로그인 완료 감지! 현재 URL: {current_url}")
                    login_success = True
                    break
            time.sleep(1)
            
        if not login_success:
            print("대기 시간이 초과되었거나 로그인이 완료되지 않았습니다.")
            browser.close()
            return
            
        time.sleep(3)
        
        print("새로운 저장소 생성 페이지로 이동합니다...")
        page.goto("https://github.com/new")
        time.sleep(4)
        
        repo_name = "navermarket"
        print(f"저장소 이름 '{repo_name}' 입력 중...")
        
        # 저장소 이름 입력창 탐색 및 기입 (다양한 백업 셀렉터 사용)
        repo_input = None
        selectors = [
            "input[data-testid='repository-name-input']",
            "input[name='repository_name']",
            "input[id*='repository-name']",
            "#repository-name"
        ]
        for sel in selectors:
            try:
                locator = page.locator(sel).first
                if locator.count() > 0:
                    repo_input = locator
                    break
            except:
                pass
                
        if repo_input:
            repo_input.fill(repo_name)
            print("저장소 이름 입력 완료.")
        else:
            print("오류: 저장소 이름 입력란을 찾지 못했습니다.")
            browser.close()
            return
            
        time.sleep(3)
        
        # 'Create repository' 버튼 클릭 (다양한 백업 셀렉터 사용)
        print("저장소 생성 버튼 클릭 시도...")
        create_btn = None
        btn_selectors = [
            "button:has-text('Create repository')",
            "button[type='submit']:has-text('Create')",
            "button[type='submit']",
            "text=Create repository"
        ]
        for b_sel in btn_selectors:
            try:
                locator = page.locator(b_sel).first
                if locator.count() > 0 and locator.is_visible():
                    create_btn = locator
                    break
            except:
                pass
                
        if create_btn:
            create_btn.click(force=True)
            print("저장소 생성 버튼 클릭 완료.")
        else:
            print("오류: 저장소 생성 버튼을 찾지 못했습니다.")
            browser.close()
            return
            
        # 저장소 생성 후 로딩 대기
        time.sleep(8)
        
        current_url = page.url
        print(f"생성 완료 후 현재 URL: {current_url}")
        
        # Git 원격 주소 추출 및 가공
        base_url = current_url.split("?")[0].split("/tree/")[0]
        if not base_url.endswith(".git"):
            git_url = base_url + ".git"
        else:
            git_url = base_url
            
        print(f"★ 획득한 Git 원격 주소: {git_url}")
        
        # 로컬에서 Git 원격 주소 연결 및 푸시
        cwd = r"c:\Users\happinich\Documents\9.vibecoding\navermarket"
        print("로컬 저장소 원격 설정 중...")
        subprocess.run("git remote remove origin", shell=True, cwd=cwd)
        subprocess.run(f"git remote add origin {git_url}", shell=True, cwd=cwd)
        
        print("깃허브로 푸시(Push)를 시도합니다...")
        # 윈도우 자격증명 팝업이 뜰 수 있도록 일반 실행
        push_res = subprocess.run("git push -u origin main", shell=True, cwd=cwd, capture_output=True, text=True)
        
        print("Push 출력:")
        print(push_res.stdout)
        print(push_res.stderr)
        
        if push_res.returncode == 0:
            print("★ 깃허브 공개 저장소 생성 및 푸시를 완전히 성공했습니다!")
        else:
            print("★ 푸시 오류 발생. Credential(자격증명) 연동 상태를 확인해 주세요.")
            
        browser.close()

if __name__ == "__main__":
    main()
