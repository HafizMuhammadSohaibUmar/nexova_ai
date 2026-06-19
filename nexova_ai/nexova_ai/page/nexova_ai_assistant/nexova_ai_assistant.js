frappe.provide("frappe.pages");
frappe.pages["nexova-ai-assistant"] = frappe.pages["nexova-ai-assistant"] || {};

frappe.pages["nexova-ai-assistant"].on_page_load = function (wrapper) {
  if ($(wrapper).find(".nexova-ai-page").length) {
    return;
  }

  const page = frappe.ui.make_app_page({
    parent: wrapper,
    title: __("Nexova AI"),
    single_column: true,
  });

  const state = {
    listening: false,
    recognition: null,
    ttsEnabled: true,
    voiceEnabled: true,
  };

  const $root = $(`
    <div class="nexova-ai-page">
      <section class="nexova-ai-shell">
        <div class="nexova-ai-toolbar">
          <div>
            <h2>${__("Nexova AI")}</h2>
            <p>${__("Ask ERPNext about sales, stock, and receivables.")}</p>
          </div>
          <button class="btn btn-default btn-sm nexova-ai-tts" type="button" aria-pressed="true">
            ${__("Voice replies: On")}
          </button>
        </div>
        <div class="nexova-ai-messages" role="log" aria-live="polite"></div>
        <form class="nexova-ai-composer">
          <button class="btn btn-default nexova-ai-mic" type="button" title="${__("Voice input")}">
            <span class="octicon octicon-device-camera-video"></span>
          </button>
          <input class="form-control nexova-ai-input" type="text" autocomplete="off" placeholder="${__("Ask: today's sales, stock balance, pending receivables")}" />
          <button class="btn btn-primary nexova-ai-send" type="submit">${__("Ask")}</button>
        </form>
      </section>
    </div>
  `);

  $(page.body).append($root);

  const $messages = $root.find(".nexova-ai-messages");
  const $input = $root.find(".nexova-ai-input");
  const $mic = $root.find(".nexova-ai-mic");
  const $send = $root.find(".nexova-ai-send");
  const $tts = $root.find(".nexova-ai-tts");

  addMessage("assistant", __("Hi. Ask me about sales, purchases, stock, receivables, payables, customers, suppliers, items, orders, invoices, or ERPNext navigation."));
  loadClientConfig();
  setupSpeechRecognition();

  $root.find(".nexova-ai-composer").on("submit", function (event) {
    event.preventDefault();
    askQuestion($input.val());
  });

  $mic.on("click", function () {
    if (!state.recognition) {
      frappe.show_alert({
        message: __("Voice input is not supported in this browser."),
        indicator: "orange",
      });
      return;
    }

    if (state.listening) {
      state.recognition.stop();
      return;
    }

    state.recognition.start();
  });

  $tts.on("click", function () {
    state.ttsEnabled = !state.ttsEnabled;
    $tts.attr("aria-pressed", state.ttsEnabled ? "true" : "false");
    $tts.text(state.ttsEnabled ? __("Voice replies: On") : __("Voice replies: Off"));
    if (!state.ttsEnabled && window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
  });

  function askQuestion(rawQuestion) {
    const question = (rawQuestion || "").trim();

    if (!question) {
      return;
    }

    addMessage("user", question);
    $input.val("");
    setLoading(true);

    frappe.call({
      method: "nexova_ai.api.ask_ai",
      args: { question },
      callback(response) {
        const answer = response.message && response.message.message
          ? response.message.message
          : __("I could not find an answer.");
        const data = response.message && response.message.data
          ? response.message.data
          : {};

        const $assistantMessage = addMessage("assistant", answer);
        renderStructuredData(data, $assistantMessage);
        speak(answer);
        handleAction(data);
      },
      error() {
        addMessage("assistant", __("Something went wrong while asking ERPNext."));
      },
      always() {
        setLoading(false);
      },
    });
  }

  function addMessage(role, text) {
    const label = role === "user" ? __("You") : __("Nexova AI");
    const $message = $(`
      <article class="nexova-ai-message nexova-ai-message-${role}">
        <div class="nexova-ai-message-label"></div>
        <div class="nexova-ai-message-text"></div>
      </article>
    `);

    $message.find(".nexova-ai-message-label").text(label);
    $message.find(".nexova-ai-message-text").text(text);
    $messages.append($message);
    $messages.scrollTop($messages.prop("scrollHeight"));
    return $message;
  }

  function renderStructuredData(data, $message) {
    if (!data || !$message) {
      return;
    }

    if (Array.isArray(data.summary_cards) && data.summary_cards.length) {
      const $cards = $('<div class="nexova-ai-result-cards"></div>');

      data.summary_cards.forEach(function (card) {
        const $card = $('<div class="nexova-ai-result-card"></div>');
        $('<div class="nexova-ai-result-card-label"></div>').text(card.label || "").appendTo($card);
        $('<div class="nexova-ai-result-card-value"></div>').text(String(card.value ?? "")).appendTo($card);
        $cards.append($card);
      });

      $message.append($cards);
    }

    if (data.table && Array.isArray(data.table.columns) && Array.isArray(data.table.rows) && data.table.rows.length) {
      const $tableWrap = $('<div class="nexova-ai-result-table-wrap"></div>');

      if (data.table.title) {
        $('<div class="nexova-ai-result-table-title"></div>').text(data.table.title).appendTo($tableWrap);
      }

      const $table = $('<table class="nexova-ai-result-table"></table>');
      const $thead = $('<thead></thead>');
      const $headRow = $('<tr></tr>');

      data.table.columns.forEach(function (column) {
        $('<th></th>').text(column || "").appendTo($headRow);
      });

      $thead.append($headRow);
      $table.append($thead);

      const $tbody = $('<tbody></tbody>');
      data.table.rows.slice(0, 10).forEach(function (row) {
        const $row = $('<tr></tr>');

        row.forEach(function (cell) {
          $('<td></td>').text(String(cell ?? "")).appendTo($row);
        });

        $tbody.append($row);
      });

      $table.append($tbody);
      $tableWrap.append($table);
      $message.append($tableWrap);
    }

    $messages.scrollTop($messages.prop("scrollHeight"));
  }

  function setLoading(isLoading) {
    $send.prop("disabled", isLoading);
    $input.prop("disabled", isLoading);
    $send.text(isLoading ? __("Asking...") : __("Ask"));
  }

  function setupSpeechRecognition() {
    if (!state.voiceEnabled) {
      $mic.prop("disabled", true).attr("title", __("Voice input is disabled for this site."));
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      $mic.prop("disabled", true).attr("title", __("Voice input is not supported in this browser."));
      return;
    }

    state.recognition = new SpeechRecognition();
    state.recognition.continuous = false;
    state.recognition.interimResults = false;
    state.recognition.lang = frappe.boot.lang || navigator.language || "en-US";

    state.recognition.onstart = function () {
      state.listening = true;
      $mic.addClass("active");
    };

    state.recognition.onend = function () {
      state.listening = false;
      $mic.removeClass("active");
    };

    state.recognition.onresult = function (event) {
      const transcript = event.results[0][0].transcript;
      $input.val(transcript).focus();
      frappe.show_alert({
        message: __("Transcript ready. Review it, then tap Ask."),
        indicator: "blue",
      });
    };
  }

  function speak(text) {
    if (!state.voiceEnabled || !state.ttsEnabled || !window.speechSynthesis) {
      return;
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = frappe.boot.lang || navigator.language || "en-US";
    window.speechSynthesis.speak(utterance);
  }

  function handleAction(data) {
    if (!data || data.action !== "navigate" || !Array.isArray(data.route)) {
      return;
    }

    setTimeout(function () {
      frappe.set_route.apply(frappe, data.route);
    }, 400);
  }

  function loadClientConfig() {
    frappe.call({
      method: "nexova_ai.api.get_client_config",
      callback(response) {
        const config = response.message || {};
        state.voiceEnabled = config.voice_enabled !== false;

        if (!state.voiceEnabled) {
          $mic.prop("disabled", true).attr("title", __("Voice input is disabled for this site."));
          state.ttsEnabled = false;
          $tts.attr("aria-pressed", "false");
          $tts.text(__("Voice replies: Off"));
        }
      },
    });
  }
};

frappe.pages["nexova-ai-assistant"].on_page_show = function (wrapper) {
  if (!$(wrapper).find(".nexova-ai-page").length) {
    frappe.pages["nexova-ai-assistant"].on_page_load(wrapper);
  }
};
