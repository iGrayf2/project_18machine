document.addEventListener("DOMContentLoaded", () => {
  const els = {
    wsStatus: document.getElementById("ws-status"),
    machineState: document.getElementById("machine-state"),

    recipesCount: document.getElementById("recipes-count"),
    recipeSelect: document.getElementById("recipe-select"),
    recipeRepeatsInput: document.getElementById("recipe-repeats-input"),

    encoderAngle: document.getElementById("encoder-angle"),
    machineRpm: document.getElementById("machine-rpm"),

    currentCycle: document.getElementById("current-cycle"),
    cyclesTotal: document.getElementById("cycles-total"),
    currentCycleTurn: document.getElementById("current-cycle-turn"),
    currentCycleTurnTarget: document.getElementById("current-cycle-turn-target"),
    currentRecipeRepeat: document.getElementById("current-recipe-repeat"),

    resetButton: document.getElementById("reset-button"),
    settingsButton: document.getElementById("settings-button"),
  };

  setWsStatusElement(els.wsStatus);

  function setMachineState(state) {
    const stateMap = {
      running: { text: "РАБОТАЕТ", className: "running" },
      paused: { text: "ПАУЗА", className: "paused" },
      idle: { text: "ОЖИДАНИЕ", className: "paused" },
      error: { text: "ОШИБКА", className: "error" },
    };

    const config = stateMap[state] || { text: "—", className: "paused" };
    els.machineState.textContent = config.text;
    els.machineState.className = `status-value ${config.className}`;
  }

  function updateRecipeSelect(recipes, selectedRecipeId) {
    if (!Array.isArray(recipes)) return;

    const currentValue = String(selectedRecipeId ?? "");
    const previousValue = els.recipeSelect.value;

    els.recipeSelect.innerHTML = "";

    if (recipes.length === 0) {
      const option = document.createElement("option");
      option.value = "";
      option.textContent = "Нет рецептов";
      els.recipeSelect.appendChild(option); 
      return;
    }

    for (const recipe of recipes) {
      const option = document.createElement("option");
      option.value = recipe.id;
      option.textContent = recipe.name;

      if (String(recipe.id) === currentValue) {
        option.selected = true;
      }

      els.recipeSelect.appendChild(option);
    }

    if (!currentValue && previousValue) {
      els.recipeSelect.value = previousValue;
    }
  }

  function renderMachineStatus(data) {
    els.recipesCount.textContent = data.recipes_count ?? 0;
    els.recipeRepeatsInput.value = data.recipe_repeats_target ?? 1;

    els.encoderAngle.textContent = data.encoder_angle ?? 0;
    els.machineRpm.textContent = data.rpm ?? 0;

    els.currentCycle.textContent = data.current_cycle_index ?? 0;
    els.cyclesTotal.textContent = data.cycles_total ?? 0;
    els.currentCycleTurn.textContent = data.current_cycle_turn ?? 0;
    els.currentCycleTurnTarget.textContent = data.current_cycle_turn_target ?? 0;
    els.currentRecipeRepeat.textContent = data.current_recipe_repeat ?? 0;

    setMachineState(data.state);
    updateRecipeSelect(data.recipes || [], data.selected_recipe_id);
  }

  function handleWsMessage(message) {
    if (!message || !message.type) return;

    switch (message.type) {
      case "machine_status":
        renderMachineStatus(message.data || {});
        break;

      case "reset_done":
        console.log("Сброс выполнен", message.data);
        break;

      case "info":
        console.log("INFO:", message.data?.message);
        break;

      case "error":
        console.error("ERROR:", message.data?.message);
        break;

      default:
        console.warn("Неизвестный тип сообщения:", message);
        break;
    }
  }

  function sendSelectedRecipe() {
    const recipeId = Number(els.recipeSelect.value);
    if (!recipeId) return;

    sendWsMessage({
      action: "select_recipe",
      recipe_id: recipeId,
    });
  }

  function sendRecipeRepeats() {
    let value = Number(els.recipeRepeatsInput.value);

    if (!Number.isInteger(value) || value < 1) {
      value = 1;
      els.recipeRepeatsInput.value = "1";
    }

    sendWsMessage({
      action: "set_recipe_repeats",
      value: value,
    });
  }

  function resetToCycle1() {
    sendWsMessage({
      action: "reset_to_cycle_1",
    });
  }

  function goToSettings() {
    window.location.href = "/settings";
  }

  function isTypingContext(target) {
    if (!target) return false;
    const tag = target.tagName?.toLowerCase();
    return tag === "input" || tag === "textarea" || tag === "select";
  }

  function changeRecipeByStep(step) {
    const select = els.recipeSelect;
    if (!select || select.options.length === 0) return;

    let index = select.selectedIndex;
    if (index < 0) index = 0;

    let nextIndex = index + step;

    if (nextIndex < 0) nextIndex = 0;
    if (nextIndex >= select.options.length) nextIndex = select.options.length - 1;

    if (nextIndex !== index) {
      select.selectedIndex = nextIndex;
      sendSelectedRecipe();
    }
  }

  setWsMessageHandler(handleWsMessage);

  els.recipeSelect.addEventListener("change", () => {
    sendSelectedRecipe();
  });

  els.recipeRepeatsInput.addEventListener("change", () => {
    sendRecipeRepeats();
  });

  els.recipeRepeatsInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      sendRecipeRepeats();
      els.recipeRepeatsInput.blur();
    }
  });

  els.resetButton.addEventListener("click", () => {
    resetToCycle1();
  });

  els.settingsButton.addEventListener("click", () => {
    goToSettings();
  });

  document.addEventListener("keydown", (event) => {
    const target = event.target;
    const typing = isTypingContext(target);

    if (event.key === "F2") {
      event.preventDefault();
      goToSettings();
      return;
    }

    if (event.key === "F5") {
      event.preventDefault();
      resetToCycle1();
      return;
    }

    if (event.key === "Escape") {
      if (target && typeof target.blur === "function") {
        target.blur();
      }
      return;
    }

    if (typing) {
      return;
    }

    if (event.key === "ArrowUp") {
      event.preventDefault();
      changeRecipeByStep(-1);
      return;
    }

    if (event.key === "ArrowDown") {
      event.preventDefault();
      changeRecipeByStep(1);
      return;
    }
  });

  connectWebSocket();
});