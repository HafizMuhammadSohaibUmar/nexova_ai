frappe.provide("frappe.pages");
frappe.pages["nexova-ai-assistant"] = frappe.pages["nexova-ai-assistant"] || {};

frappe.pages["nexova-ai-assistant"].on_page_load = function (wrapper) {
  const page = frappe.ui.make_app_page({
    parent: wrapper,
    title: __("Nexova AI"),
    single_column: true,
  });

  const state = {
    listening: false,
    recognition: null,
    ttsEnabled: true,
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

  addMessage("assistant", __("Hi. Ask me about today's sales, stock balance, or pending receivables."));
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

        addMessage("assistant", answer);
        speak(answer);
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
  }

  function setLoading(isLoading) {
    $send.prop("disabled", isLoading);
    $input.prop("disabled", isLoading);
    $send.text(isLoading ? __("Asking...") : __("Ask"));
  }

  function setupSpeechRecognition() {
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
      askQuestion(transcript);
    };
  }

  function speak(text) {
    if (!state.ttsEnabled || !window.speechSynthesis) {
      return;
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = frappe.boot.lang || navigator.language || "en-US";
    window.speechSynthesis.speak(utterance);
  }
};
