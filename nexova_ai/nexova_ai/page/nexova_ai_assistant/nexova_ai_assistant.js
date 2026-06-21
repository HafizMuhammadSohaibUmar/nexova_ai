frappe.provide("frappe.pages");
frappe.pages["nexova-ai-assistant"] = frappe.pages["nexova-ai-assistant"] || {};

frappe.pages["nexova-ai-assistant"].on_page_load = function (wrapper) {
  if ($(wrapper).find(".nexova-ai-page").length) {
    return;
  }

  const page = frappe.ui.make_app_page({
    parent: wrapper,
    title: __("Invoxia AI"),
    single_column: true,
  });

  const state = {
    listening: false,
    recognition: null,
    recognitionLanguage: null,
    supportsServerStt: false,
    audioContext: null,
    mediaStream: null,
    recorderSource: null,
    recorderProcessor: null,
    recordingBuffers: [],
    recordingSampleRate: 16000,
    ttsEnabled: true,
    voiceEnabled: true,
  };

  const $root = $(`
    <div class="nexova-ai-page">
      <section class="nexova-ai-shell">
        <div class="nexova-ai-toolbar">
          <div class="nexova-ai-brand">
            <img class="nexova-ai-brand-mark" src="/assets/nexova_ai/branding/invoxia-mark.svg" alt="${__("Invoxia AI")}" />
            <div>
              <h2>${__("Invoxia AI")}</h2>
              <p>${__("Ask ERPNext about sales, stock, and receivables.")}</p>
            </div>
          </div>
          <button class="btn btn-default btn-sm nexova-ai-tts" type="button" aria-pressed="true">
            ${__("Voice replies: On")}
          </button>
        </div>
        <div class="nexova-ai-messages" role="log" aria-live="polite"></div>
        <form class="nexova-ai-composer">
          <button class="btn btn-default nexova-ai-mic" type="button" title="${__("Voice input")}">
            ${micIcon()}
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
  loadClientConfig(setupSpeechRecognition);

  $root.find(".nexova-ai-composer").on("submit", function (event) {
    event.preventDefault();
    askQuestion($input.val());
  });

  $mic.on("click", function () {
    if (state.supportsServerStt) {
      toggleServerRecording();
      return;
    }

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

  function toggleServerRecording() {
    if (!navigator.mediaDevices || !window.AudioContext && !window.webkitAudioContext) {
      frappe.show_alert({
        message: __("Audio recording is not supported in this browser."),
        indicator: "orange",
      });
      return;
    }

    if (state.listening) {
      stopServerRecording();
      return;
    }

    navigator.mediaDevices.getUserMedia({ audio: true }).then(function (stream) {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      const audioContext = new AudioContextClass();
      const source = audioContext.createMediaStreamSource(stream);
      const processor = audioContext.createScriptProcessor(4096, 1, 1);

      state.mediaStream = stream;
      state.audioContext = audioContext;
      state.recorderSource = source;
      state.recorderProcessor = processor;
      state.recordingBuffers = [];
      state.recordingSampleRate = audioContext.sampleRate;

      processor.onaudioprocess = function (event) {
        if (!state.listening) {
          return;
        }
        state.recordingBuffers.push(new Float32Array(event.inputBuffer.getChannelData(0)));
      };

      source.connect(processor);
      processor.connect(audioContext.destination);

      state.listening = true;
      $mic.addClass("active");
      frappe.show_alert({
        message: __("Listening. Tap the mic again to stop."),
        indicator: "blue",
      });
    }).catch(function () {
      frappe.show_alert({
        message: __("Microphone permission was not granted."),
        indicator: "red",
      });
    });
  }

  function stopServerRecording() {
    const processor = state.recorderProcessor;
    const source = state.recorderSource;
    const audioContext = state.audioContext;
    const stream = state.mediaStream;

    state.listening = false;
    $mic.removeClass("active");

    if (processor) {
      processor.disconnect();
      processor.onaudioprocess = null;
    }
    if (source) {
      source.disconnect();
    }
    if (stream) {
      stream.getTracks().forEach(function (track) {
        track.stop();
      });
    }
    if (audioContext && audioContext.state !== "closed") {
      audioContext.close();
    }

    state.recorderProcessor = null;
    state.recorderSource = null;
    state.audioContext = null;
    state.mediaStream = null;

    transcribeServerAudio();
  }

  function transcribeServerAudio() {
    if (!state.recordingBuffers.length) {
      return;
    }

    const audioBlob = encodeWavBlob(state.recordingBuffers, state.recordingSampleRate, 16000);
    state.recordingBuffers = [];
    const formData = new FormData();
    formData.append("audio", audioBlob, "voice.wav");
    setLoading(true);

    fetch("/api/method/nexova_ai.api.transcribe_audio", {
      method: "POST",
      body: formData,
      headers: {
        "X-Frappe-CSRF-Token": frappe.csrf_token,
      },
    }).then(function (response) {
      return response.json();
    }).then(function (response) {
      const message = response.message || {};
      const transcript = (message.transcript || "").trim();
      if (!transcript) {
        addMessage("assistant", __("I could not hear a clear command. Please try again."));
        return;
      }
      $input.val(transcript).focus();
      frappe.show_alert({
        message: __("Transcript ready. Review it, then tap Ask."),
        indicator: "blue",
      });
    }).catch(function () {
      addMessage("assistant", __("Voice transcription failed. Please try again or type your question."));
    }).finally(function () {
      setLoading(false);
    });
  }

  function encodeWavBlob(buffers, inputSampleRate, outputSampleRate) {
    const merged = mergeAudioBuffers(buffers);
    const samples = downsampleAudio(merged, inputSampleRate, outputSampleRate);
    const wav = new ArrayBuffer(44 + samples.length * 2);
    const view = new DataView(wav);

    writeAscii(view, 0, "RIFF");
    view.setUint32(4, 36 + samples.length * 2, true);
    writeAscii(view, 8, "WAVE");
    writeAscii(view, 12, "fmt ");
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, 1, true);
    view.setUint32(24, outputSampleRate, true);
    view.setUint32(28, outputSampleRate * 2, true);
    view.setUint16(32, 2, true);
    view.setUint16(34, 16, true);
    writeAscii(view, 36, "data");
    view.setUint32(40, samples.length * 2, true);

    let offset = 44;
    for (let i = 0; i < samples.length; i++) {
      const sample = Math.max(-1, Math.min(1, samples[i]));
      view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7fff, true);
      offset += 2;
    }

    return new Blob([view], { type: "audio/wav" });
  }

  function mergeAudioBuffers(buffers) {
    const length = buffers.reduce(function (total, buffer) {
      return total + buffer.length;
    }, 0);
    const merged = new Float32Array(length);
    let offset = 0;
    buffers.forEach(function (buffer) {
      merged.set(buffer, offset);
      offset += buffer.length;
    });
    return merged;
  }

  function downsampleAudio(samples, inputSampleRate, outputSampleRate) {
    if (inputSampleRate === outputSampleRate) {
      return samples;
    }

    const ratio = inputSampleRate / outputSampleRate;
    const length = Math.round(samples.length / ratio);
    const result = new Float32Array(length);
    let inputOffset = 0;

    for (let i = 0; i < length; i++) {
      const nextOffset = Math.round((i + 1) * ratio);
      let total = 0;
      let count = 0;
      for (let j = inputOffset; j < nextOffset && j < samples.length; j++) {
        total += samples[j];
        count++;
      }
      result[i] = count ? total / count : 0;
      inputOffset = nextOffset;
    }

    return result;
  }

  function writeAscii(view, offset, text) {
    for (let i = 0; i < text.length; i++) {
      view.setUint8(offset + i, text.charCodeAt(i));
    }
  }

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
    const label = role === "user" ? __("You") : __("Invoxia AI");
    const $message = $(`
      <article class="nexova-ai-message nexova-ai-message-${role}">
        <div class="nexova-ai-message-label">
          ${role === "assistant" ? assistantIcon() : ""}
          <span></span>
        </div>
        <div class="nexova-ai-message-text"></div>
      </article>
    `);

    $message.find(".nexova-ai-message-label span").text(label);
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

    if (state.supportsServerStt) {
      $mic.prop("disabled", false).attr("title", __("Record voice command"));
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
    state.recognition.maxAlternatives = 5;
    state.recognition.lang = state.recognitionLanguage || frappe.boot.lang || navigator.language || "en-PK";

    state.recognition.onstart = function () {
      state.listening = true;
      $mic.addClass("active");
    };

    state.recognition.onend = function () {
      state.listening = false;
      $mic.removeClass("active");
    };

    state.recognition.onresult = function (event) {
      const alternatives = Array.from(event.results[0] || []);
      const best = alternatives.sort(function (a, b) {
        return (b.confidence || 0) - (a.confidence || 0);
      })[0];
      const transcript = best ? best.transcript : "";
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
      if (data.route_options && Object.keys(data.route_options).length) {
        frappe.route_options = data.route_options;
      }
      frappe.set_route.apply(frappe, data.route);
    }, 400);
  }

  function loadClientConfig(done) {
    frappe.call({
      method: "nexova_ai.api.get_client_config",
      callback(response) {
        const config = response.message || {};
        state.voiceEnabled = config.voice_enabled !== false;
        state.recognitionLanguage = config.voice && config.voice.recognition_language
          ? config.voice.recognition_language
          : null;
        state.supportsServerStt = Boolean(config.voice && config.voice.supports_server_stt);

        if (!state.voiceEnabled) {
          $mic.prop("disabled", true).attr("title", __("Voice input is disabled for this site."));
          state.ttsEnabled = false;
          $tts.attr("aria-pressed", "false");
          $tts.text(__("Voice replies: Off"));
        }
      },
      always() {
        if (state.supportsServerStt) {
          $mic.prop("disabled", false).attr("title", __("Record voice command"));
        }
        if (typeof done === "function") {
          done();
        }
      },
    });
  }

  function micIcon() {
    return `
      <svg class="nexova-ai-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
        <path d="M12 14a3 3 0 0 0 3-3V6a3 3 0 0 0-6 0v5a3 3 0 0 0 3 3Z"></path>
        <path d="M19 10v1a7 7 0 0 1-14 0v-1"></path>
        <path d="M12 18v4"></path>
        <path d="M8 22h8"></path>
      </svg>
    `;
  }

  function assistantIcon() {
    return `
      <svg class="nexova-ai-label-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
        <rect x="5" y="7" width="14" height="12" rx="3"></rect>
        <path d="M12 3v4"></path>
        <path d="M8.5 12h.01"></path>
        <path d="M15.5 12h.01"></path>
        <path d="M9 16h6"></path>
      </svg>
    `;
  }
};

frappe.pages["nexova-ai-assistant"].on_page_show = function (wrapper) {
  if (!$(wrapper).find(".nexova-ai-page").length) {
    frappe.pages["nexova-ai-assistant"].on_page_load(wrapper);
  }
};
