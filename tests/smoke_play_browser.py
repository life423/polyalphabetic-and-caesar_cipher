"""Exercise mission gameplay, persistence, recovery and tool isolation."""
import argparse
import json
from pathlib import Path

from playwright.sync_api import expect, sync_playwright


def campaign_checks(browser, url, output):
    root = Path(__file__).resolve().parents[1] / 'static/missions'
    manifest = json.loads((root / 'campaign.json').read_text())
    cases = [json.loads((root / name).read_text()) for name in manifest['missions']]
    context = browser.new_context()
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(url)
    page.locator('#play-tab').click()
    expect(page.locator('#campaign-cases button')).to_have_count(5)
    expect(page.locator('[data-case="2"]')).to_be_disabled()
    # All five cases are loaded before play, so navigation works offline.
    expect(page.locator('#mission-content')).to_be_visible()
    context.set_offline(True)
    for index, mission in enumerate(cases):
        expect(page.locator('#mission-title')).to_have_text(mission['title'])
        expect(page.locator(f'[data-case="{index + 1}"]')).to_have_attribute('aria-current', 'step')
        expect(page.locator('#mission-complete')).to_be_hidden()
        if index == 1:
            # A reveal advances the story but never earns solved credit.
            page.locator('#mission-reveal').click()
            page.locator('#mission-reveal-yes').click()
            expect(page.locator('#campaign-progress')).to_have_text('1 of 5 cases solved · 1 revealed')
        else:
            mapping = {c: p for c, p in zip(mission['ciphertext'], mission['solution']) if c.isalpha()}
            if index == 2:
                first_cipher, first_plain = next(iter(mapping.items()))
                page.locator('#guess-' + first_cipher).fill(first_plain)
                page.locator('[data-case="1"]').click()
                page.locator('[data-case="3"]').click()
                expect(page.locator('#guess-' + first_cipher)).to_have_value(first_plain)
            for cipher, plain in mapping.items():
                page.locator('#guess-' + cipher).fill(plain)
            page.locator('#mission-check').click()
            expect(page.locator('#mission-complete-title')).to_have_text('Case solved')
        for width in (320, 390, 768, 1440):
            page.set_viewport_size({'width': width, 'height': 1000})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (index, width)
            page.screenshot(path=str(output / f'case-{index + 1}-{width}.png'), full_page=True)
        if index < 4:
            page.locator('#mission-next').click()
    expect(page.locator('#campaign-complete')).to_be_visible()
    expect(page.locator('#campaign-progress')).to_have_text('4 of 5 cases solved · 1 revealed')
    expect(page.locator('#mission-next')).to_be_hidden()
    context.set_offline(False)
    page.reload()
    page.locator('#play-tab').click()
    expect(page.locator('#mission-title')).to_have_text(cases[4]['title'])
    expect(page.locator('#campaign-complete')).to_be_visible()
    # Resetting a prior case leaves other progress and access intact.
    page.locator('[data-case="1"]').click()
    page.locator('#mission-reset').click()
    page.locator('#mission-reset-yes').click()
    expect(page.locator('#campaign-progress')).to_have_text('3 of 5 cases solved · 1 revealed')
    expect(page.locator('[data-case="5"]')).to_be_enabled()
    expect(page.locator('#campaign-complete')).to_be_hidden()
    page.locator('[data-case="3"]').click()
    expect(page.locator('#mission-complete-title')).to_have_text('Case solved')
    expect(page.locator('#mission-undo')).to_be_disabled()  # Previous case's undo never leaks.
    page.locator('#campaign-resume').click()
    expect(page.locator('#mission-title')).to_have_text(cases[0]['title'])
    # Restore the reset via its own history, without touching case three.
    page.locator('#mission-undo').click()
    expect(page.locator('#campaign-complete')).to_be_visible()
    page.locator('[data-case="2"]').click()
    page.locator('#mission-reset').click()
    page.locator('#mission-reset-yes').click()
    second = cases[1]
    for cipher, plain in {c: p for c, p in zip(second['ciphertext'], second['solution']) if c.isalpha()}.items():
        page.locator('#guess-' + cipher).fill(plain)
    page.locator('#mission-check').click()
    expect(page.locator('#campaign-progress')).to_have_text('5 of 5 cases solved · 0 revealed')
    expect(page.locator('#campaign-complete')).to_be_visible()
    # A standalone v1 save migrates without replaying the first case.
    migrated = browser.new_context()
    first = cases[0]
    save = {'guesses': {c: p for c, p in zip(first['ciphertext'], first['solution']) if c.isalpha()},
            'clues': 1, 'checked': True, 'revealed': False}
    migrated.add_init_script('localStorage.setItem("ciphercraft.play.observatory-note.v1", ' + json.dumps(json.dumps(save)) + ')')
    old = migrated.new_page()
    old.goto(url)
    old.locator('#play-tab').click()
    expect(old.locator('#mission-complete-title')).to_have_text('Case solved')
    expect(old.locator('[data-case="2"]')).to_be_enabled()
    expect(old.locator('[data-case="3"]')).to_be_disabled()
    # Invalid saved flags and malformed ledger cannot falsely solve/unlock a case.
    corrupt = browser.new_context()
    corrupt.add_init_script('''localStorage.setItem('ciphercraft.campaign.missing-astronomer.v1', '{"unlocked":999,"selected":-1}');
        localStorage.setItem('ciphercraft.play.observatory-note.v1', '{"checked":true,"guesses":{"A":"T","L":"T"},"clues":99}');''')
    bad = corrupt.new_page()
    bad.goto(url)
    bad.locator('#play-tab').click()
    expect(bad.locator('#mission-content')).to_be_visible()
    expect(bad.locator('#mission-complete')).to_be_hidden()
    expect(bad.locator('[data-case="2"]')).to_be_disabled()
    expect(bad.locator('#campaign-progress')).to_have_text('0 of 5 cases solved · 0 revealed')
    assert not errors, errors
    context.close()
    migrated.close()
    corrupt.close()


def check(url, screenshots):
    output = Path(screenshots)
    output.mkdir(parents=True, exist_ok=True)
    mission = json.loads((Path(__file__).resolve().parents[1] / 'static/missions/observatory-note.json').read_text())
    mapping = {c: p for c, p in zip(mission['ciphertext'], mission['solution']) if c.isalpha()}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context()
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(url)
        expect(page.locator('#identify')).to_be_enabled(timeout=90000)
        page.locator('#manual-tab').click()
        page.locator('#message').fill('Preserve this message.')
        page.locator('#key').fill('9')
        page.locator('#encrypt').click()
        expect(page.locator('#status')).to_have_text('Encryption complete.')
        result = page.locator('#result').text_content()
        page.locator('#play-tab').click()
        expect(page.locator('#mission-content')).to_be_visible()
        expect(page.locator('#tools-workspace')).to_be_hidden()
        page.locator('#mission-check').click()
        expect(page.locator('#mission-status')).to_contain_text('still blank')
        expect(page.locator('#mission-complete')).to_be_hidden()
        page.locator('#mission-try-word').click()
        expect(page.locator('#guess-A')).to_have_value('T')
        expect(page.locator('#guess-O')).to_have_value('H')
        expect(page.locator('#guess-L')).to_have_value('E')
        expect(page.locator('#mission-first-move')).to_be_hidden()
        page.locator('#mission-undo').click()
        expect(page.locator('#mission-first-move')).to_be_visible()
        page.locator('#guess-A').fill('t')
        expect(page.locator('#guess-A')).to_have_value('T')
        for cell in page.locator('[data-letter="A"] .mission-guess').all():
            expect(cell).to_have_text('T')
        page.locator('#guess-L').fill('T')
        expect(page.locator('#mission-status')).to_contain_text('already assigned')
        expect(page.locator('#guess-L')).to_have_value('')
        page.locator('#guess-L').fill('4')
        expect(page.locator('#mission-status')).to_contain_text('Use one English letter')
        page.locator('#guess-L').fill('E')
        page.locator('#mission-undo').click()
        expect(page.locator('#guess-L')).to_have_value('')
        expect(page.locator('#guess-A')).to_have_value('T')
        page.locator('#mission-clue').click()
        expect(page.locator('#mission-clue-list')).to_contain_text('AOL appears 3 times')
        page.locator('#mission-reset').click()
        page.locator('#mission-reset-no').click()
        expect(page.locator('#guess-A')).to_have_value('T')
        page.locator('#mission-reset').click()
        page.locator('#mission-reset-yes').click()
        expect(page.locator('#guess-A')).to_have_value('')
        page.locator('#mission-undo').click()
        expect(page.locator('#guess-A')).to_have_value('T')
        expect(page.locator('#mission-clue-list li')).to_have_count(1)
        page.locator('#manual-tab').click()
        expect(page.locator('#message')).to_have_value('Preserve this message.')
        expect(page.locator('#key')).to_have_value('9')
        expect(page.locator('#result')).to_have_text(result)
        # Arrow keys pass through Messages to Play without changing tool content.
        page.locator('#manual-tab').focus()
        page.keyboard.press('ArrowRight')
        expect(page.locator('#messages-tab')).to_be_focused()
        page.keyboard.press('ArrowRight')
        expect(page.locator('#play-tab')).to_be_focused()
        expect(page.locator('#guess-A')).to_have_value('T')
        page.reload()
        page.locator('#play-tab').click()
        expect(page.locator('#guess-A')).to_have_value('T')
        expect(page.locator('#mission-clue-list li')).to_have_count(1)
        for width in (320, 390, 768, 1440):
            page.set_viewport_size({'width': width, 'height': 1000})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), width
            assert page.locator('#guess-A').bounding_box()['height'] >= 44
            page.screenshot(path=str(output / f'mission-{width}.png'), full_page=True)
        # All entries filled incorrectly must never earn completion.
        page.locator('#mission-reset').click()
        page.locator('#mission-reset-yes').click()
        for letter, plain in mapping.items():
            wrong = chr((ord(plain) - 65 + 1) % 26 + 65)
            page.locator('#guess-' + letter).fill(wrong)
        page.locator('#mission-check').click()
        expect(page.locator('#mission-status')).to_contain_text('not quite right')
        expect(page.locator('#mission-complete')).to_be_hidden()
        page.locator('#mission-reset').click()
        page.locator('#mission-reset-yes').click()
        for letter, plain in mapping.items():
            page.locator('#guess-' + letter).fill(plain)
        page.locator('#mission-check').click()
        expect(page.locator('#mission-complete-title')).to_have_text('Case solved')
        expect(page.locator('#mission-ending')).to_contain_text('brass compass')
        page.reload()
        page.locator('#play-tab').click()
        expect(page.locator('#mission-complete')).to_be_visible()
        page.locator('#mission-reveal').click()
        page.locator('#mission-reveal-no').click()
        expect(page.locator('#mission-complete-title')).to_have_text('Case solved')
        page.locator('#mission-reveal').click()
        page.locator('#mission-reveal-yes').click()
        expect(page.locator('#mission-complete-title')).to_have_text('Note revealed')
        page.locator('#mission-undo').click()
        expect(page.locator('#mission-complete-title')).to_have_text('Case solved')
        # Block mission content first, then retry while the tool engine is broken.
        isolated = browser.new_context()
        isolated.route('**/worker.js', lambda route: route.abort())
        isolated.route('**/missions/*.json', lambda route: route.abort())
        recovery = isolated.new_page()
        recovery.goto(url)
        recovery.locator('#play-tab').click()
        expect(recovery.locator('#mission-error')).to_be_visible()
        isolated.unroute('**/missions/*.json')
        recovery.locator('#mission-retry').click()
        expect(recovery.locator('#mission-content')).to_be_visible()
        # Saving failure is explicit and must not prevent playing.
        blocked = browser.new_context()
        blocked.add_init_script("Storage.prototype.setItem = () => {throw new DOMException('blocked', 'SecurityError')}")
        memory = blocked.new_page()
        memory.goto(url)
        memory.locator('#play-tab').click()
        expect(memory.locator('#mission-storage')).to_contain_text('storage is unavailable')
        memory.locator('#guess-A').fill('T')
        expect(memory.locator('#mission-progress')).to_contain_text('1 of')
        assert not errors, errors
        campaign_checks(browser, url, output)
        browser.close()
    print('Play checks passed: five-case campaign, offline navigation, progression/replay, migration, saved-state recovery, tool isolation and four viewport widths.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='http://localhost:8502')
    parser.add_argument('--screenshots', default='dist/play-checks')
    args = parser.parse_args()
    check(args.url, args.screenshots)
