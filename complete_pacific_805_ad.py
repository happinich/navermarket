import json
import os
import re
import sys
import time
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parent
LOG_PATH = ROOT / "pacific_805_ad_run.log"

K_WEB_OPEN = "\uc6f9\ube0c\ub77c\uc6b0\uc800\uc5d0\uc11c \uc5f4\uae30"
K_CONFIRM = "\ud655\uc778"
K_AD_SEND = "\uad11\uace0\uc804\uc1a1"
K_AD_SUBMIT = "\uad11\uace0\ud558\uae30"
K_VERIFY_SELECT = "\uac80\uc99d\ubc29\uc2dd \uc120\ud0dd"
K_OLD_PROMO = "\uad6c\ud64d\ubcf4\ud655\uc778\uc11c"
K_PERSON = "\uac1c\uc778"
K_SELF = "\ubcf8\uc778"
K_ONLINE = "\uc628\ub77c\uc778 \uc804\uc1a1"
K_WRITE_PROMO = "\ud64d\ubcf4\ud655\uc778\uc11c \uc791\uc131"
K_WRITE_PROMO_MODAL = "\ud64d\ubcf4\ud655\uc778\uc11c \uc791\uc131\ud558\uae30"
K_PRIVACY = "\uac1c\uc778\uc815\ubcf4 \uc218\uc9d1 \ubc0f \uc774\uc6a9"
K_AGREE = "\ub3d9\uc758\ud569\ub2c8\ub2e4"
K_PAYMENT = "1,900\uc6d0 \uacb0\uc81c"


def log(message: str) -> None:
    print(message, flush=True)


def save_state(page, stem: str) -> None:
    page.screenshot(path=str(ROOT / f"{stem}.png"), full_page=True)
    (ROOT / f"{stem}.html").write_text(page.content(), encoding="utf-8")


def click_first_visible(locator, label: str, timeout: int = 8000) -> bool:
    deadline = time.time() + timeout / 1000
    last_error = None
    while time.time() < deadline:
        count = locator.count()
        for i in range(count):
            item = locator.nth(i)
            try:
                if item.is_visible():
                    item.click(force=True, timeout=1500)
                    log(f"clicked: {label}")
                    return True
            except Exception as exc:
                last_error = exc
        time.sleep(0.3)
    log(f"could not click {label}: {last_error}")
    return False


def dispatch_input_events(locator) -> None:
    locator.evaluate(
        "el => { el.dispatchEvent(new Event('input', { bubbles: true })); "
        "el.dispatchEvent(new Event('change', { bubbles: true })); }"
    )


def draw_signature(page) -> None:
    canvas = page.locator("canvas").last
    canvas.wait_for(state="visible", timeout=10000)
    box = canvas.bounding_box()
    if not box:
        raise RuntimeError("signature canvas has no bounding box")

    # Draw a simple signature-like path. Real pointer events are important here:
    # directly painting pixels does not always update the app's form state.
    x = box["x"]
    y = box["y"]
    w = box["width"]
    h = box["height"]
    points = [
        (0.18, 0.58),
        (0.27, 0.38),
        (0.36, 0.63),
        (0.46, 0.34),
        (0.56, 0.60),
        (0.68, 0.42),
        (0.80, 0.56),
    ]
    page.mouse.move(x + w * points[0][0], y + h * points[0][1])
    page.mouse.down()
    for px, py in points[1:]:
        page.mouse.move(x + w * px, y + h * py, steps=8)
    page.mouse.up()
    time.sleep(0.5)
    log("signature drawn with mouse events")


def main() -> None:
    sys.stdout = open(LOG_PATH, "w", encoding="utf-8", buffering=1)
    sys.stderr = sys.stdout

    config_path = ROOT / "config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    username = config["gongsilclub"]["username"]
    password = config["gongsilclub"]["password"]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        page.on("dialog", lambda dialog: (log(f"dialog: {dialog.message}"), dialog.accept()))

        log("opening entry page")
        page.goto("https://www.gongsilclub.co.kr/", wait_until="load", timeout=30000)
        time.sleep(2)

        if page.get_by_text(K_WEB_OPEN, exact=True).count() > 0 or page.locator(".button-item-2").count() > 0:
            try:
                with context.expect_page(timeout=3000) as popup_info:
                    if page.get_by_text(K_WEB_OPEN, exact=True).count() > 0:
                        page.get_by_text(K_WEB_OPEN, exact=True).first.click(force=True)
                    else:
                        page.locator(".button-item-2").first.click(force=True)
                page = popup_info.value
                page.wait_for_load_state("load", timeout=15000)
                log("web browser entry opened a new page")
            except PlaywrightTimeoutError:
                if page.get_by_text(K_WEB_OPEN, exact=True).count() > 0:
                    page.get_by_text(K_WEB_OPEN, exact=True).first.click(force=True)
                else:
                    page.locator(".button-item-2").first.click(force=True)
                page.wait_for_load_state("load", timeout=15000)
                log("web browser entry opened in the same page")
            time.sleep(3)

        if page.locator("input[placeholder*='ID']").count() == 0:
            page.goto("https://www.gongsilclub.co.kr/group/login/", wait_until="load", timeout=30000)
            time.sleep(3)

        if page.locator("input[placeholder*='ID']").count() > 0:
            page.locator("input[placeholder*='ID']").first.fill(username)
            page.locator("input[type='password']").first.fill(password)
            page.locator("input[type='password']").first.press("Enter")
            log("login submitted")
            time.sleep(5)

        if page.get_by_text("다른 PC에서 로그인 중입니다").count() > 0:
            click_first_visible(page.get_by_text(K_CONFIRM, exact=True), "duplicate-login confirm")
            time.sleep(4)

        log("opening management page")
        page.goto("https://www.gongsilclub.co.kr/group/management/", wait_until="load", timeout=30000)
        time.sleep(5)
        save_state(page, "pacific_805_management_before")

        card = page.locator("div.border-gray50").filter(has_text=re.compile("13170")).first
        card.wait_for(state="visible", timeout=15000)
        card_text = card.inner_text()
        log("target card found:")
        log(card_text)

        if "\uad11\uace0\uc911" in card_text or "\ub124\uc774\ubc84 \ubd80\ub3d9\uc0b0" in card_text:
            save_state(page, "pacific_805_already_advertised")
            log("target already appears to be advertised; stopping")
            browser.close()
            return

        if not click_first_visible(card.get_by_text(K_AD_SEND, exact=True), "광고전송"):
            raise RuntimeError("광고전송 button not found on target card")
        time.sleep(3)

        # Some flows show an intermediate submit button before verification choices.
        if page.get_by_text(K_AD_SUBMIT, exact=True).count() > 0:
            click_first_visible(page.get_by_text(K_AD_SUBMIT, exact=True), "광고하기")
            time.sleep(6)

        page.get_by_text(K_VERIFY_SELECT).first.wait_for(state="visible", timeout=20000)
        save_state(page, "pacific_805_verify_choices")

        old_promo_card = page.locator("form div.border-gray50").filter(has_text=re.compile(K_OLD_PROMO)).last
        old_promo_card.wait_for(state="visible", timeout=10000)
        old_promo_card.click(force=True)
        log("selected 구홍보확인서")
        time.sleep(5)

        # Fill/confirm required verification information.
        name_input = page.locator("input[name='verification.oname']").first
        name_input.wait_for(state="visible", timeout=10000)
        if not name_input.input_value().strip():
            name_input.fill("이성구")
            dispatch_input_events(name_input)

        click_first_visible(page.locator("label").filter(has_text=re.compile(f"^{K_PERSON}$")), "개인")
        time.sleep(0.5)

        relation_dropdown = page.locator("xpath=//div[contains(., '의뢰인과 소유자와의 관계')]/following::div[contains(@style, 'cursor: pointer')][1]")
        if relation_dropdown.count() > 0:
            relation_dropdown.first.click(force=True)
            time.sleep(1)
            click_first_visible(page.get_by_text(K_SELF, exact=True), "본인")

        click_first_visible(page.locator("label").filter(has_text=re.compile(f"^{K_ONLINE}$")), "온라인 전송")
        time.sleep(1)
        save_state(page, "pacific_805_verify_filled")

        if not click_first_visible(page.locator("div.button").filter(has_text=re.compile(K_WRITE_PROMO)), "홍보확인서 작성"):
            raise RuntimeError("홍보확인서 작성 button not found")
        time.sleep(2)

        page.get_by_text(K_WRITE_PROMO_MODAL).first.wait_for(state="visible", timeout=10000)
        draw_signature(page)
        save_state(page, "pacific_805_signature_drawn")

        if not click_first_visible(page.locator("div.button").filter(has_text=re.compile(f"^{K_CONFIRM}$")), "signature 확인"):
            raise RuntimeError("signature confirmation button not found")
        time.sleep(4)

        # Confirm the form accepted the signature.
        save_state(page, "pacific_805_after_signature_confirm")

        click_first_visible(page.get_by_text("Gpay", exact=False), "Gpay option", timeout=3000)
        if page.get_by_text("새로고침", exact=True).count() > 0:
            click_first_visible(page.get_by_text("새로고침", exact=True), "Gpay 새로고침", timeout=3000)
            time.sleep(1)

        agree_text = page.get_by_text(K_PRIVACY, exact=False).first
        if agree_text.count() > 0:
            agree_text.click(force=True)
            log("opened/selected 개인정보 동의")
            time.sleep(2)

        # If a terms popup opens, accept it.
        if page.get_by_text(K_AGREE).count() > 0:
            click_first_visible(page.get_by_text(K_AGREE, exact=False), "약관 동의")
            time.sleep(3)

        save_state(page, "pacific_805_before_final_payment")

        pay_button = page.locator("div.button").filter(has_text=re.compile(K_PAYMENT)).first
        pay_button.wait_for(state="visible", timeout=10000)
        try:
            pay_button.click(force=True)
        except Exception:
            pay_button.evaluate("el => el.click()")
        log("clicked final 1,900원 결제")
        time.sleep(10)

        save_state(page, "pacific_805_ad_complete")
        log("completed final state capture")

        browser.close()


if __name__ == "__main__":
    main()
