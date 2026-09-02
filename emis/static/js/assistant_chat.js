/* =========================================================
   EMIS AI Assistant — chat engine
   Streaming, state visibility, affordances, commands, errors
   ========================================================= */

(function () {
  'use strict';

  const cfg = window.EMIS_ASSISTANT || {};
  const STORAGE_KEY = 'emis_ai_history_' + (cfg.portal || 'shared');

  let state = {
    history: [],        // [{role, content}] sent to the API + persisted
    streaming: false,
    lastUserText: '',
    lastAiEl: null,     // .ai-msg element currently streaming into
    lastAiText: '',     // accumulated plain text of the streaming answer
    abort: null,
    firstTokenTimer: null,
    restored: false,
  };

  /* ---------------- helpers ---------------- */

  function $(sel, root) { return (root || document).querySelector(sel); }
  function $$(sel, root) { return Array.from((root || document).querySelectorAll(sel)); }

  function esc(s) {
    return String(s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  function inlineFormat(s) {
    return s
      .replace(/`([^`\n]+)`/g, '<code>$1</code>')
      .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
      .replace(/(^|[^*])\*([^*\n]+)\*/g, '$1<em>$2</em>')
      .replace(/\[([^\]]+)\]\(([^)\s]+)\)/g,
        '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
  }

  /* Safe, dependency-free markdown-lite renderer */
  function markdown(src) {
    const lines = esc(src).split('\n');
    const html = [];
    let inList = null;

    const closeList = function () {
      if (inList) { html.push('</' + inList + '>'); inList = null; }
    };

    for (const raw of lines) {
      const line = raw.replace(/\r$/, '');

      if (html.length && html[html.length - 1] === '<pre><code>') {
        if (/^```/.test(line)) html.push('</code></pre>');
        else html.push(line + '\n');
        continue;
      }

      if (/^```/.test(line)) {
        closeList();
        html.push('<pre><code>');
        continue;
      }

      const h = line.match(/^(#{1,3})\s+(.*)$/);
      if (h) { closeList(); html.push('<h' + h[1].length + '>' + inlineFormat(h[2]) + '</h' + h[1].length + '>'); continue; }

      const li = line.match(/^\s*[-*]\s+(.+)$/);
      if (li) {
        if (inList !== 'ul') { closeList(); html.push('<ul>'); inList = 'ul'; }
        html.push('<li>' + inlineFormat(li[1]) + '</li>');
        continue;
      }

      const oli = line.match(/^\s*\d+\.\s+(.+)$/);
      if (oli) {
        if (inList !== 'ol') { closeList(); html.push('<ol>'); inList = 'ol'; }
        html.push('<li>' + inlineFormat(oli[1]) + '</li>');
        continue;
      }

      closeList();
      if (line.trim() === '') continue;
      html.push('<p>' + inlineFormat(line) + '</p>');
    }
    closeList();
    return html.join('');
  }

  function scrollToBottom(force) {
    const scroll = $('#aiScroll');
    if (!scroll) return;
    const near = scroll.scrollHeight - scroll.scrollTop - scroll.clientHeight < 90;
    if (force || near) scroll.scrollTop = scroll.scrollHeight;
  }

  function saveHistory() {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(state.history)); } catch (e) { /* private mode */ }
  }

  function loadHistory() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : [];
    } catch (e) { return []; }
  }

  /* ---------------- rendering ---------------- */

  function cloneTpl(id) {
    const tpl = $('#' + id);
    return tpl.content.firstElementChild.cloneNode(true);
  }

  function addUserMessage(text) {
    const row = cloneTpl('aiTplUser');
    $('.ai-bubble-text', row).textContent = text;
    const meta = $('.ai-msg-meta', row);
    meta.textContent = cfg.userName || 'You';
    meta.appendChild(document.createTextNode(' · ' + new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })));
    $('#aiMessages').appendChild(row);
    scrollToBottom(true);
    return row;
  }

  function addAssistantMessage() {
    const row = cloneTpl('aiTplAssistant');
    $('#aiMessages').appendChild(row);
    scrollToBottom(true);
    return row;
  }

  function addErrorMessage(title, msg) {
    const row = cloneTpl('aiTplError');
    $('.ai-error-title', row).textContent = title;
    $('.ai-error-msg', row).textContent = msg;
    $('#aiMessages').appendChild(row);
    scrollToBottom(true);
    return row;
  }

  function setTyping(row, show, label) {
    const t = $('.ai-typing', row);
    t.hidden = !show;
    if (label) $('.ai-typing-label', t).textContent = label;
  }

  function setTool(row, show, label) {
    const t = $('.ai-tool-chip', row);
    t.hidden = !show;
    if (label) $('.ai-tool-label', t).textContent = label;
  }

  function appendToken(row, text) {
    const body = $('.ai-bubble-text', row);
    const caret = body.querySelector('.ai-caret');
    if (caret) caret.remove();
    body.appendChild(document.createTextNode(text));
    const c = document.createElement('span');
    c.className = 'ai-caret';
    body.appendChild(c);
    scrollToBottom();
  }

  function finishStreaming(row) {
    const body = $('.ai-bubble-text', row);
    const caret = body.querySelector('.ai-caret');
    if (caret) caret.remove();
    body.innerHTML = markdown(body.textContent || '');
    setTyping(row, false);
    setTool(row, false);
    const actions = $('.ai-msg-actions', row);
    if (actions) actions.hidden = false;
  }

  /* ---------------- API ---------------- */

  function apiUrl() {
    return cfg.apiUrl || '/assistant/api/chat/';
  }

  async function send(prompt, mode) {
    if (state.streaming) return;
    if (!prompt || !prompt.trim()) return;
    prompt = prompt.trim();

    state.streaming = true;
    state.lastUserText = prompt;
    setSendBusy(true);

    if (mode !== 'regenerate') {
      state.history.push({ role: 'user', content: prompt });
      addUserMessage(prompt);
    }
    if (mode === 'edit') {
      /* previous user message was removed; push the edited prompt */
      state.history.push({ role: 'user', content: prompt });
      addUserMessage(prompt);
    }

    const row = addAssistantMessage();
    state.lastAiEl = row;
    state.lastAiText = '';
    $('.ai-msg-actions', row).hidden = true;
    setTyping(row, true, 'thinking');
    setTool(row, false);

    const controller = new AbortController();
    state.abort = controller;

    let received = false;
    state.firstTokenTimer = setTimeout(() => {
      if (!received && state.streaming) {
        controller.abort();
        failStream(row, {
          title: 'The assistant is taking a while',
          msg: 'It can take a moment to gather the latest records. Please try again, or ask a shorter question.',
        });
      }
    }, 30000);

    try {
      const resp = await fetch(apiUrl(), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken() },
        body: JSON.stringify({ messages: state.history.slice(-20) }),
        signal: controller.signal,
      });

      if (!resp.ok) {
        failStream(row, {
          title: 'Something went wrong on our side',
          msg: 'The assistant service returned an error. Please try again in a moment — your message was not lost.',
        });
        return;
      }

      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        received = true;
        clearTimeout(state.firstTokenTimer);
        buffer += decoder.decode(value, { stream: true });

        const events = buffer.split('\n\n');
        buffer = events.pop();

        for (const chunk of events) {
          const line = chunk.split('\n').find((l) => l.startsWith('data:'));
          if (!line) continue;
          let evt;
          try { evt = JSON.parse(line.slice(5).trim()); } catch (e) { continue; }

          if (evt.type === 'tool') {
            setTyping(row, false);
            setTool(row, true, evt.label || 'Processing');
          } else if (evt.type === 'token') {
            setTyping(row, false);
            setTool(row, false);
            state.lastAiText += evt.text;
            appendToken(row, evt.text);
          } else if (evt.type === 'error') {
            failStream(row, { title: 'The assistant had trouble answering', msg: evt.message || 'Please try again.' });
            return;
          } else if (evt.type === 'done') {
            finishStreaming(row);
            state.history.push({ role: 'assistant', content: state.lastAiText });
            saveHistory();
            state.streaming = false;
            setSendBusy(false);
            return;
          }
        }
      }

      /* stream ended without done event */
      if (state.streaming) {
        if (state.lastAiText) {
          finishStreaming(row);
          state.history.push({ role: 'assistant', content: state.lastAiText });
          saveHistory();
        } else {
          failStream(row, {
            title: 'The connection closed early',
            msg: 'The response was interrupted. Please try again.',
          });
        }
        state.streaming = false;
        setSendBusy(false);
      }
    } catch (err) {
      clearTimeout(state.firstTokenTimer);
      if (err.name === 'AbortError') return; /* handled by timeout branch */
      failStream(row, {
        title: "Can't reach the assistant",
        msg: 'Check your internet connection and try again.',
      });
    }
  }

  function failStream(row, info) {
    clearTimeout(state.firstTokenTimer);
    state.streaming = false;
    setSendBusy(false);
    if (row && row.parentNode) {
      row.remove();
      const errRow = addErrorMessage(info.title, info.msg);
      errRow.dataset.retryPrompt = state.lastUserText;
    }
    scrollToBottom(true);
  }

  function csrfToken() {
    const m = document.cookie.match(/csrftoken=([^;]+)/);
    return m ? m[1] : '';
  }

  function setSendBusy(busy) {
    const btn = $('#aiSendBtn');
    if (!btn) return;
    btn.disabled = busy;
    btn.innerHTML = busy ? '<span class="ai-spinner"></span>' : '<i class="bi bi-arrow-up"></i>';
  }

  /* ---------------- actions ---------------- */

  async function doAction(action, row) {
    if (state.streaming) return;

    const bubbleText = $('.ai-bubble-text', row);
    const content = bubbleText ? bubbleText.textContent.trim() : '';

    if (action === 'copy') {
      const btn = $('[data-action="copy"]', row);
      try {
        await navigator.clipboard.writeText(content);
      } catch (e) {
        const ta = document.createElement('textarea');
        ta.value = content;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        ta.remove();
      }
      if (btn) {
        btn.dataset.state = 'done';
        btn.innerHTML = '<i class="bi bi-check-lg"></i><span>Copied</span>';
        setTimeout(() => {
          btn.dataset.state = '';
          btn.innerHTML = '<i class="bi bi-clipboard"></i><span>Copy</span>';
        }, 1600);
      }
      return;
    }

    if (action === 'regenerate') {
      const lastUser = [...state.history].reverse().find((m) => m.role === 'user');
      if (!lastUser) return;
      row.remove();
      /* drop the previous assistant entry so the API does not see it twice */
      state.history = state.history.filter((m) => !(m.role === 'assistant' && state.history.indexOf(m) === state.history.length - 1));
      send(lastUser.content, 'regenerate');
      return;
    }

    if (action === 'edit') {
      const lastUser = [...state.history].reverse().find((m) => m.role === 'user');
      if (!lastUser) return;
      row.remove();
      state.history = state.history.filter(
        (m) => !(m.role === 'user' && state.history.indexOf(m) === state.history.length - 1)
      );
      const input = $('#aiInput');
      input.value = lastUser.content;
      autogrow(input);
      input.focus();
      return;
    }

    if (action === 'retry') {
      const prompt = row.dataset.retryPrompt || state.lastUserText;
      row.remove();
      if (prompt) send(prompt, 'retry');
    }
  }

  /* ---------------- composer & commands ---------------- */

  const COMMANDS = {
    '/help': 'What can you help me with?',
    '/notices': 'What are the latest notices?',
    '/programs': 'Which programs does the college offer?',
    '/fees': 'How much are the fees for each program?',
    '/clear': null,
  };

  function toggleCmdMenu(show) {
    const menu = $('#aiCmdMenu');
    if (menu) menu.hidden = !show;
  }

  function runCommand(cmd) {
    toggleCmdMenu(false);
    if (cmd === '/clear') {
      if (state.streaming) state.abort && state.abort.abort();
      state.history = [];
      state.streaming = false;
      setSendBusy(false);
      const msgs = $('#aiMessages');
      msgs.innerHTML = '';
      const hero = $('#aiHero');
      if (hero) msgs.appendChild(hero);
      saveHistory();
      return;
    }
    const prompt = COMMANDS[cmd];
    if (prompt) send(prompt, 'command');
  }

  function autogrow(ta) {
    ta.style.height = 'auto';
    ta.style.height = Math.min(ta.scrollHeight, 160) + 'px';
  }

  /* ---------------- restore ---------------- */

  function restore() {
    const history = loadHistory();
    if (!history.length) return;
    state.history = history;
    for (const m of history) {
      if (m.role === 'user') addUserMessage(m.content);
      else {
        const row = addAssistantMessage();
        const body = $('.ai-bubble-text', row);
        body.innerHTML = markdown(m.content);
        $('.ai-msg-actions', row).hidden = false;
      }
    }
    scrollToBottom(true);
  }

  /* ---------------- init ---------------- */

  function init() {
    const form = $('#aiForm');
    const input = $('#aiInput');
    const messages = $('#aiMessages');
    const cmdMenu = $('#aiCmdMenu');

    if (!form || !input || !messages) return;

    restore();

    /* compose */
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const value = input.value.trim();
      if (!value || state.streaming) return;
      input.value = '';
      autogrow(input);
      toggleCmdMenu(false);
      send(value, 'new');
    });

    input.addEventListener('input', () => autogrow(input));

    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        form.requestSubmit();
      }
    });

    input.addEventListener('input', () => {
      if (input.value.startsWith('/')) toggleCmdMenu(true);
      else if (!cmdMenu || cmdMenu.hidden) { /* keep */ }
      else toggleCmdMenu(false);
    });

    $('#aiCmdToggle').addEventListener('click', () => {
      toggleCmdMenu(cmdMenu ? cmdMenu.hidden : false);
    });

    document.addEventListener('click', (e) => {
      if (!e.target.closest('.ai-composer-wrap')) toggleCmdMenu(false);
    });

    /* command items */
    $$('.ai-cmd-item').forEach((item) => {
      item.addEventListener('click', () => runCommand(item.dataset.command));
    });

    /* hero chips + error suggestion chips (delegated) */
    messages.addEventListener('click', (e) => {
      const chip = e.target.closest('.ai-chip[data-prompt]');
      if (chip && !state.streaming) send(chip.dataset.prompt, 'chip');
    });

    /* message action buttons (delegated) */
    messages.addEventListener('click', (e) => {
      const btn = e.target.closest('.ai-act[data-action]');
      if (!btn) return;
      const row = btn.closest('.ai-msg');
      if (row) doAction(btn.dataset.action, row);
    });

    /* Enter on a chip should not submit the form */
    $$('.ai-chip').forEach((c) => c.setAttribute('type', 'button'));

    setSendBusy(false);
    scrollToBottom(true);
  }

  window.EMISAssistant = { init: init };
})();