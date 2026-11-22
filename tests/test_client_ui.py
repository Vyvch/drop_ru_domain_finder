"""
Автоматические тесты клиентской части (Практика 8, Критерии 7–11).
Проверяют интерфейс, компоненты, валидацию, защиту от дабл-клика и сквозной сценарий.
"""
import json
import os
import re
import shutil
import subprocess
import unittest

INDEX_HTML = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates', 'index.html'))
NODE = shutil.which("node")

NODE_TEST_RUNNER = r"""
const vm = require('vm');
let input = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => { input += chunk; });
process.stdin.on('end', async () => {
    const { script, testScenario } = JSON.parse(input);
    
    // Minimal DOM Mock environment
    const elements = new Map();
    function createMockElement(id, tag = 'div') {
        const el = {
            id,
            tagName: tag.toUpperCase(),
            textContent: '',
            innerText: '',
            value: '',
            hidden: false,
            disabled: false,
            style: {},
            classList: {
                _classes: new Set(),
                add: function(...cls) { cls.forEach(c => this._classes.add(c)); },
                remove: function(...cls) { cls.forEach(c => this._classes.delete(c)); },
                toggle: function(c, force) {
                    if (force !== undefined) {
                        if (force) this._classes.add(c); else this._classes.delete(c);
                        return force;
                    }
                    if (this._classes.has(c)) { this._classes.delete(c); return false; }
                    this._classes.add(c); return true;
                },
                contains: function(c) { return this._classes.has(c); }
            },
            attributes: {},
            setAttribute: function(name, val) { this.attributes[name] = String(val); if (name === 'disabled') this.disabled = true; },
            removeAttribute: function(name) { delete this.attributes[name]; if (name === 'disabled') this.disabled = false; },
            getAttribute: function(name) { return this.attributes[name] || null; },
            children: [],
            appendChild: function(c) { this.children.push(c); return c; },
            removeChild: function(c) { this.children = this.children.filter(x => x !== c); return c; },
            click: function() {
                this._clicked = true;
                if (this._listeners && this._listeners['click']) {
                    this._listeners['click'].forEach(fn => fn({ target: this, preventDefault: () => {} }));
                }
            },
            replaceChildren: function(...c) { this.children = c; },
            addEventListener: function(event, handler) {
                this._listeners = this._listeners || {};
                this._listeners[event] = this._listeners[event] || [];
                this._listeners[event].push(handler);
            },
            dispatchEvent: function(event) {
                if (this._listeners && this._listeners[event]) {
                    this._listeners[event].forEach(fn => fn({ target: this, preventDefault: () => {} }));
                }
            },
            querySelector: function(sel) { return createMockElement(sel); },
            querySelectorAll: function(sel) { return [createMockElement(sel)]; },
            showModal: function() { this.open = true; },
            close: function() { this.open = false; }
        };
        elements.set(id, el);
        return el;
    }

    // Pre-populate known IDs from index.html
    [
        'search-input', 'search-btn', 'search-btn-spinner', 'search-btn-text',
        'search-error', 'regex-toggle', 'search-count', 'all-loader',
        'domain-grid', 'empty-state', 'pagination', 'page-input', 'total-pages',
        'btn-prev', 'btn-next', 'domain-dialog', 'domain-dialog-title',
        'domain-dialog-date', 'top-loader', 'top-table', 'top-body', 'top-table-container',
        'all', 'top', 'tab-btn-all', 'tab-btn-top-today', 'tab-btn-top-tomorrow',
        'header-total-count', 'date-filters', 'export-csv-btn'
    ].forEach(id => createMockElement(id));

    const documentMock = {
        getElementById: id => elements.get(id) || createMockElement(id),
        createElement: tag => createMockElement('dyn_' + Math.random(), tag),
        createTextNode: txt => ({ nodeType: 3, textContent: txt }),
        querySelectorAll: sel => Array.from(elements.values()),
        body: createMockElement('body')
    };

    const networkCalls = [];
    const fetchMock = async (url, opts = {}) => {
        networkCalls.push({ url, opts, time: Date.now() });
        if (url.includes('regex=invalid')) {
            return {
                ok: false,
                status: 400,
                json: async () => ({ detail: 'Ошибка синтаксиса RE2' })
            };
        }
        if (url.includes('status=500')) {
            return {
                ok: false,
                status: 500,
                json: async () => ({ error: 'Internal Server Error' })
            };
        }
        if (url.includes('empty')) {
            return {
                ok: true,
                status: 200,
                json: async () => []
            };
        }
        return {
            ok: true,
            status: 200,
            json: async () => [
                { domain: 'shop-test.ru', date: '2026-11-23' },
                { domain: 'shop-online.ru', date: '2026-11-23' }
            ]
        };
    };

    const context = vm.createContext({
        URL,
        URLSearchParams,
        AbortController,
        console,
        setTimeout,
        clearTimeout,
        document: documentMock,
        window: {
            addEventListener: () => {},
            location: { search: '' }
        },
        fetch: fetchMock,
        networkCalls,
        elements
    });

    try {
        // Run core client script
        vm.runInContext(script, context);
        // Run test assertion scenario
        const runScenario = vm.runInContext('(async () => { ' + testScenario + ' })', context);
        const result = await runScenario();
        process.stdout.write(JSON.stringify({ success: true, result }));
    } catch (e) {
        process.stderr.write(String((e && e.stack) || e));
        process.exit(1);
    }
});
"""


def run_client_test(scenario_code: str) -> dict:
    with open(INDEX_HTML, encoding="utf-8") as f:
        html = f.read()

    # Extract all scripts including wayback-core
    wayback_match = re.search(r'<script id="wayback-core">(.*?)</script>', html, re.DOTALL)
    wayback_core = wayback_match.group(1) if wayback_match else ""
    
    scripts = re.findall(r"<script(?![^>]*id=\"wayback-core\")[^>]*>(.*?)</script>", html, re.DOTALL)
    client_script = wayback_core + "\n" + "\n".join(scripts)

    payload = json.dumps({"script": client_script, "testScenario": scenario_code})
    proc = subprocess.run(
        [NODE, "-e", NODE_TEST_RUNNER],
        input=payload,
        text=True,
        capture_output=True,
        timeout=15,
    )
    if proc.returncode != 0:
        raise AssertionError(f"Client test failed:\nSTDOUT: {proc.stdout}\nSTDERR: {proc.stderr}")
    return json.loads(proc.stdout)


class TestClientUI(unittest.TestCase):
    """Тестирование клиентской части на соответствие критериям Практики 8."""

    def test_criterion_7_prevent_duplicate_submit(self):
        """Критерий 7: Исключены случайные повторные действия при отправке формы (дабл-клик/Enter)."""
        scenario = """
        // Reset call count
        networkCalls.length = 0;
        rawQuery = 'shop';
        isSubmitting = false;

        // First click triggers search
        const p1 = submitSearch();
        
        // Immediate second click while first is in-flight must be ignored!
        const p2 = submitSearch();
        
        // Immediate third click must also be ignored
        const p3 = submitSearch();

        await Promise.all([p1, p2, p3]);

        const searchBtn = document.getElementById('search-btn');
        return {
            totalCalls: networkCalls.length,
            btnWasDisabledDuringSubmit: !isSubmitting // finished
        };
        """
        res = run_client_test(scenario)["result"]
        # Exactly 1 network request must have been made despite 3 rapid calls!
        self.assertEqual(res["totalCalls"], 1, "Защита от повторной отправки не сработала: отправлен дублирующий запрос!")

    def test_criterion_8_component_interactions_and_modal(self):
        """Критерий 8: Нажатия кнопок, переключение вкладок, открытие/закрытие модалок."""
        scenario = """
        // 1. Switch tabs
        const tabBtn = document.getElementById('tab-btn-top-today');
        const mockEvt = { target: tabBtn };
        switchTab('top', mockEvt, 'today');
        const allTab = document.getElementById('all');
        const topTab = document.getElementById('top');
        const tabsSwitched = (allTab.style.display === 'none' && topTab.style.display === 'flex');

        // 2. Open Domain Dialog
        const testDomain = { domain: 'market-cloud.ru', date: '2026-11-25' };
        openDomainDialog(testDomain);
        const titleEl = document.getElementById('domain-dialog-title');
        const dialogTitleMatch = (titleEl.textContent === 'market-cloud.ru');

        return { tabsSwitched, dialogTitleMatch };
        """
        res = run_client_test(scenario)["result"]
        self.assertTrue(res["tabsSwitched"], "Переключение вкладок не изменило видимость контента")
        self.assertTrue(res["dialogTitleMatch"], "Диалог открылся с неверным заголовком домена")

    def test_criterion_9_form_validation_and_errors(self):
        """Критерий 9: Валидация форм, некорректный ввод RE2 и сообщения об ошибках."""
        scenario = """
        const errorBox = document.getElementById('search-error');
        const searchInput = document.getElementById('search-input');
        
        // 1. Initially error is hidden
        clearSearchError();
        const initialHidden = errorBox.hidden;

        // 2. Simulate RE2 validation error response (400)
        const seq = ++requestSeq;
        await fetchRegex('invalid[regex', seq);
        const hasErrorShown = !errorBox.hidden && errorBox.textContent.length > 0;
        const inputMarkedInvalid = searchInput.classList.contains('invalid') || searchInput.classList.contains('input-error');

        // 3. Clear error
        clearSearchError();
        const cleared = errorBox.hidden;

        return { initialHidden, hasErrorShown, inputMarkedInvalid, cleared };
        """
        res = run_client_test(scenario)["result"]
        self.assertTrue(res["initialHidden"])
        self.assertTrue(res["hasErrorShown"], "Сообщение об ошибке валидации RE2 не отобразилось")
        self.assertTrue(res["cleared"], "Ошибка не очистилась после вызова clearSearchError")

    def test_criterion_10_ui_states_loading_empty_error_success(self):
        """Критерий 10: Состояния интерфейса: загрузка, пустые данные, успех, ошибка."""
        scenario = """
        // 1. Success state: domains loaded
        allDomains = [{ domain: 'alpha.ru', date: '2026-11-23' }];
        applyFilters();
        const grid = document.getElementById('domain-grid');
        const successCardsRendered = grid.children.length > 0;
        const emptyHiddenOnSuccess = document.getElementById('empty-state').classList.contains('hidden');

        // 2. Empty state: filter produces 0 results
        allDomains = [];
        applyFilters();
        const emptyVisibleOnZero = !document.getElementById('empty-state').classList.contains('hidden');

        // 3. Error state display
        showSearchError('HTTP 500 Server Error');
        const errorVisible = !document.getElementById('search-error').hidden;

        return { successCardsRendered, emptyHiddenOnSuccess, emptyVisibleOnZero, errorVisible };
        """
        res = run_client_test(scenario)["result"]
        self.assertTrue(res["successCardsRendered"], "Карточки успеха не отрендерились")
        self.assertTrue(res["emptyVisibleOnZero"], "Пустое состояние (empty-state) не показалось при 0 результатов")
        self.assertTrue(res["errorVisible"], "Блок ошибки не отобразился при ошибке")

    def test_criterion_11_full_user_scenario_e2e(self):
        """Критерий 11: Сквозной сценарий пользователя: поиск -> фильтр -> клик карточки -> экспорт."""
        scenario = """
        // Step 1: User types search query
        handleSearch('shop');
        
        // Step 2: Fetch and apply domains
        await fetchRegex('shop', ++requestSeq);
        const domainsCount = filteredDomains.length;
        
        // Step 3: User clicks first domain to inspect
        const first = filteredDomains[0];
        openDomainDialog(first);
        const dialogTitle = document.getElementById('domain-dialog-title').textContent;
        
        // Step 4: Export CSV triggered
        let exportExecuted = false;
        try {
            exportToCsv();
            exportExecuted = true;
        } catch (e) {
            exportExecuted = false;
        }

        return {
            domainsFound: domainsCount > 0,
            dialogOpenedWithCorrectDomain: dialogTitle === first.domain,
            exportExecuted
        };
        """
        res = run_client_test(scenario)["result"]
        self.assertTrue(res["domainsFound"], "Сценарий: поиск не вернул домены")
        self.assertTrue(res["dialogOpenedWithCorrectDomain"], "Сценарий: клик по карточке не открыл диалог с доменом")
        self.assertTrue(res["exportExecuted"], "Сценарий: экспорт в CSV вызвал ошибку")


if __name__ == '__main__':
    unittest.main()
