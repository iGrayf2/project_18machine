document.addEventListener("DOMContentLoaded", () => {
  const els = {
    recipeList: document.getElementById("recipe-list"),
    recipeNameInput: document.getElementById("recipe-name-input"),
    recipeRepeatsInput: document.getElementById("recipe-repeats-settings-input"),

    newRecipeBtn: document.getElementById("new-recipe-btn"),
    copyRecipeBtn: document.getElementById("copy-recipe-btn"),
    deleteRecipeBtn: document.getElementById("delete-recipe-btn"),

    cycleList: document.getElementById("cycle-list"),
    cycleTurnsInput: document.getElementById("cycle-turns-input"),

    newCycleBtn: document.getElementById("new-cycle-btn"),
    copyCycleBtn: document.getElementById("copy-cycle-btn"),
    deleteCycleBtn: document.getElementById("delete-cycle-btn"),
    moveCycleUpBtn: document.getElementById("move-cycle-up-btn"),
    moveCycleDownBtn: document.getElementById("move-cycle-down-btn"),

    clearCycleBtn: document.getElementById("clear-cycle-btn"),

    eventsTbody: document.getElementById("events-tbody"),

    saveSettingsBtn: document.getElementById("save-settings-btn"),
    backButton: document.getElementById("back-button"),
  };

  const state = {
    selectedRecipeIndex: 0,
    selectedCycleIndex: 0,
    selectedTableRowIndex: 0,
    copiedRow: null,
    recipes: [],
    nextRecipeId: 1000,
    nextCycleId: 10000,
  };

  function createEmptyEvents() {
    return Array.from({ length: 80 }, (_, index) => ({
      valve: index + 1,
      event: "",
      angle: 0,
    }));
  }

  function recalcNextIds() {
    let maxRecipeId = 0;
    let maxCycleId = 0;

    for (const recipe of state.recipes) {
      maxRecipeId = Math.max(maxRecipeId, Number(recipe.id) || 0);
      for (const cycle of recipe.cycles || []) {
        maxCycleId = Math.max(maxCycleId, Number(cycle.id) || 0);
      }
    }

    state.nextRecipeId = maxRecipeId + 1;
    state.nextCycleId = maxCycleId + 1;
  }

  async function loadRecipesFromBackend() {
    const response = await fetch("/api/recipes");
    if (!response.ok) {
      throw new Error("Не удалось загрузить рецепты");
    }

    const data = await response.json();
    state.recipes = Array.isArray(data.recipes) ? data.recipes : [];
    recalcNextIds();
    clampSelectedIndexes();
    renderAll();
  }

  async function saveRecipesToBackend() {
    const response = await fetch("/api/recipes/save", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ recipes: state.recipes }),
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || "Не удалось сохранить рецепты");
    }

    return await response.json();
  }

  function getSelectedRecipe() {
    return state.recipes[state.selectedRecipeIndex] || null;
  }

  function getSelectedCycle() {
    const recipe = getSelectedRecipe();
    if (!recipe) return null;
    return recipe.cycles[state.selectedCycleIndex] || null;
  }

  function getSelectedRow() {
    const cycle = getSelectedCycle();
    if (!cycle) return null;
    return cycle.events[state.selectedTableRowIndex] || null;
  }

  function clampSelectedIndexes() {
    if (state.recipes.length === 0) {
      state.selectedRecipeIndex = -1;
      state.selectedCycleIndex = -1;
      state.selectedTableRowIndex = 0;
      return;
    }

    if (state.selectedRecipeIndex < 0) state.selectedRecipeIndex = 0;
    if (state.selectedRecipeIndex >= state.recipes.length) {
      state.selectedRecipeIndex = state.recipes.length - 1;
    }

    const recipe = getSelectedRecipe();
    if (!recipe || recipe.cycles.length === 0) {
      state.selectedCycleIndex = -1;
    } else {
      if (state.selectedCycleIndex < 0) state.selectedCycleIndex = 0;
      if (state.selectedCycleIndex >= recipe.cycles.length) {
        state.selectedCycleIndex = recipe.cycles.length - 1;
      }
    }

    if (state.selectedTableRowIndex < 0) state.selectedTableRowIndex = 0;
    if (state.selectedTableRowIndex > 79) state.selectedTableRowIndex = 79;
  }

  function renderRecipeList() {
    clampSelectedIndexes();
    els.recipeList.innerHTML = "";

    state.recipes.forEach((recipe, index) => {
      const item = document.createElement("div");
      item.className = `list-item ${index === state.selectedRecipeIndex ? "active" : ""}`;
      item.textContent = recipe.name;
      item.dataset.index = index;

      item.addEventListener("click", () => {
        state.selectedRecipeIndex = index;
        state.selectedCycleIndex = 0;
        renderAll();
      });

      els.recipeList.appendChild(item);
    });

    const recipe = getSelectedRecipe();
    if (recipe) {
      els.recipeNameInput.value = recipe.name;
      els.recipeRepeatsInput.value = recipe.repeats;
    } else {
      els.recipeNameInput.value = "";
      els.recipeRepeatsInput.value = 1;
    }
  }

  function renderCycleList() {
    els.cycleList.innerHTML = "";
    const recipe = getSelectedRecipe();

    if (!recipe) {
      els.cycleTurnsInput.value = 1;
      return;
    }

    recipe.cycles.forEach((cycle, index) => {
      const item = document.createElement("div");
      item.className = `list-item ${index === state.selectedCycleIndex ? "active" : ""}`;
      item.textContent = `Цикл ${index + 1} | Оборотов: ${cycle.turns}`;
      item.dataset.index = index;

      item.addEventListener("click", () => {
        state.selectedCycleIndex = index;
        renderAll();
      });

      els.cycleList.appendChild(item);
    });

    const cycle = getSelectedCycle();
    els.cycleTurnsInput.value = cycle ? cycle.turns : 1;
  }

  function renderEventsTable() {
    els.eventsTbody.innerHTML = "";
    const cycle = getSelectedCycle();

    if (!cycle) return;

    cycle.events.forEach((row, index) => {
      const tr = document.createElement("tr");
      tr.dataset.rowIndex = index;

      if (index === state.selectedTableRowIndex) {
        tr.classList.add("active-row");
      }

      const valveTd = document.createElement("td");
      valveTd.innerHTML = `<span class="valve-number">${row.valve}</span>`;

      const eventTd = document.createElement("td");
      const eventSelect = document.createElement("select");
      eventSelect.className = "event-select";
      eventSelect.dataset.rowIndex = index;

      const options = [
        { value: "", text: "—" },
        { value: "on", text: "ВКЛ" },
        { value: "off", text: "ВЫКЛ" },
      ];

      options.forEach((opt) => {
        const option = document.createElement("option");
        option.value = opt.value;
        option.textContent = opt.text;
        if (row.event === opt.value) option.selected = true;
        eventSelect.appendChild(option);
      });

      eventSelect.addEventListener("focus", () => {
        state.selectedTableRowIndex = index;
        renderEventsTable();
      });

      eventSelect.addEventListener("change", () => {
        row.event = eventSelect.value;
      });

      eventTd.appendChild(eventSelect);

      const angleTd = document.createElement("td");
      const angleInput = document.createElement("input");
      angleInput.className = "angle-input";
      angleInput.type = "number";
      angleInput.min = "0";
      angleInput.max = "360";
      angleInput.step = "1";
      angleInput.value = row.angle;
      angleInput.dataset.rowIndex = index;

      angleInput.addEventListener("focus", () => {
        state.selectedTableRowIndex = index;
        renderEventsTable();
      });

      angleInput.addEventListener("change", () => {
        let value = Number(angleInput.value);
        if (!Number.isInteger(value) || value < 0) value = 0;
        if (value > 360) value = 360;
        angleInput.value = value;
        row.angle = value;
      });

      angleTd.appendChild(angleInput);

      tr.appendChild(valveTd);
      tr.appendChild(eventTd);
      tr.appendChild(angleTd);

      tr.addEventListener("click", () => {
        state.selectedTableRowIndex = index;
        renderEventsTable();
      });

      els.eventsTbody.appendChild(tr);
    });

    scrollSelectedRowIntoView();
  }

  function renderAll() {
    clampSelectedIndexes();
    renderRecipeList();
    renderCycleList();
    renderEventsTable();
  }

  function scrollSelectedRowIntoView() {
    const row = els.eventsTbody.querySelector(
      `tr[data-row-index="${state.selectedTableRowIndex}"]`
    );
    if (row) {
      row.scrollIntoView({ block: "nearest" });
    }
  }

  function addRecipe() {
    const recipeId = state.nextRecipeId++;
    const cycleId = state.nextCycleId++;

    state.recipes.push({
      id: recipeId,
      name: `Новый рецепт ${recipeId}`,
      repeats: 1,
      cycles: [
        {
          id: cycleId,
          turns: 1,
          events: createEmptyEvents(),
        },
      ],
    });

    state.selectedRecipeIndex = state.recipes.length - 1;
    state.selectedCycleIndex = 0;
    renderAll();
    els.recipeNameInput.focus();
    els.recipeNameInput.select();
  }

  function copyRecipe() {
    const recipe = getSelectedRecipe();
    if (!recipe) return;

    const clone = JSON.parse(JSON.stringify(recipe));
    clone.id = state.nextRecipeId++;
    clone.name = `${recipe.name} копия`;

    clone.cycles = clone.cycles.map((cycle) => ({
      ...cycle,
      id: state.nextCycleId++,
    }));

    state.recipes.push(clone);
    state.selectedRecipeIndex = state.recipes.length - 1;
    state.selectedCycleIndex = 0;
    renderAll();
  }

  function deleteRecipe() {
    if (state.recipes.length === 0) return;

    state.recipes.splice(state.selectedRecipeIndex, 1);

    if (state.selectedRecipeIndex >= state.recipes.length) {
      state.selectedRecipeIndex = state.recipes.length - 1;
    }

    state.selectedCycleIndex = 0;
    renderAll();
  }

  function addCycle() {
    const recipe = getSelectedRecipe();
    if (!recipe) return;

    recipe.cycles.push({
      id: state.nextCycleId++,
      turns: 1,
      events: createEmptyEvents(),
    });

    state.selectedCycleIndex = recipe.cycles.length - 1;
    renderAll();
    els.cycleTurnsInput.focus();
    els.cycleTurnsInput.select();
  }

  function copyCycle() {
    const recipe = getSelectedRecipe();
    const cycle = getSelectedCycle();
    if (!recipe || !cycle) return;

    const clone = JSON.parse(JSON.stringify(cycle));
    clone.id = state.nextCycleId++;

    recipe.cycles.splice(state.selectedCycleIndex + 1, 0, clone);
    state.selectedCycleIndex += 1;
    renderAll();
  }

  function deleteCycle() {
    const recipe = getSelectedRecipe();
    if (!recipe || recipe.cycles.length <= 1) return;

    recipe.cycles.splice(state.selectedCycleIndex, 1);

    if (state.selectedCycleIndex >= recipe.cycles.length) {
      state.selectedCycleIndex = recipe.cycles.length - 1;
    }

    renderAll();
  }

  function moveCycle(step) {
    const recipe = getSelectedRecipe();
    if (!recipe) return;

    const index = state.selectedCycleIndex;
    const newIndex = index + step;

    if (newIndex < 0 || newIndex >= recipe.cycles.length) return;

    const temp = recipe.cycles[index];
    recipe.cycles[index] = recipe.cycles[newIndex];
    recipe.cycles[newIndex] = temp;

    state.selectedCycleIndex = newIndex;
    renderAll();
  }

  function clearCycle() {
    const cycle = getSelectedCycle();
    if (!cycle) return;

    cycle.events = createEmptyEvents();
    renderEventsTable();
  }

  function saveRecipeMeta() {
    const recipe = getSelectedRecipe();
    if (!recipe) return;

    recipe.name = els.recipeNameInput.value.trim() || "Без названия";

    let repeats = Number(els.recipeRepeatsInput.value);
    if (!Number.isInteger(repeats) || repeats < 1) repeats = 1;
    els.recipeRepeatsInput.value = repeats;
    recipe.repeats = repeats;

    renderRecipeList();
  }

  function saveCycleMeta() {
    const cycle = getSelectedCycle();
    if (!cycle) return;

    let turns = Number(els.cycleTurnsInput.value);
    if (!Number.isInteger(turns) || turns < 1) turns = 1;
    els.cycleTurnsInput.value = turns;
    cycle.turns = turns;

    renderCycleList();
  }

  async function saveAll() {
    saveRecipeMeta();
    saveCycleMeta();

    if (!state.recipes.length) {
      alert("Нет рецептов для сохранения");
      return;
    }

    const hasEmptyRecipe = state.recipes.some((recipe) => !recipe.cycles || !recipe.cycles.length);
    if (hasEmptyRecipe) {
      alert("Нельзя сохранить рецепт без циклов");
      return;
    }

    try {
      await saveRecipesToBackend();
      alert("Сохранено");
    } catch (error) {
      console.error(error);
      alert(`Ошибка сохранения: ${error.message}`);
    }
  }

  function goBack() {
    window.location.href = "/";
  }

  function isTypingContext(target) {
    if (!target) return false;
    const tag = target.tagName?.toLowerCase();
    return tag === "input" || tag === "textarea" || tag === "select";
  }

  function selectRecipeByStep(step) {
    if (state.recipes.length === 0) return;

    state.selectedRecipeIndex += step;
    if (state.selectedRecipeIndex < 0) state.selectedRecipeIndex = 0;
    if (state.selectedRecipeIndex >= state.recipes.length) {
      state.selectedRecipeIndex = state.recipes.length - 1;
    }

    state.selectedCycleIndex = 0;
    renderAll();
  }

  function selectCycleByStep(step) {
    const recipe = getSelectedRecipe();
    if (!recipe || recipe.cycles.length === 0) return;

    state.selectedCycleIndex += step;
    if (state.selectedCycleIndex < 0) state.selectedCycleIndex = 0;
    if (state.selectedCycleIndex >= recipe.cycles.length) {
      state.selectedCycleIndex = recipe.cycles.length - 1;
    }

    renderAll();
  }

  function selectTableRowByStep(step) {
    state.selectedTableRowIndex += step;
    if (state.selectedTableRowIndex < 0) state.selectedTableRowIndex = 0;
    if (state.selectedTableRowIndex > 79) state.selectedTableRowIndex = 79;

    renderEventsTable();
  }

  function setSelectedRowEvent(value) {
    const row = getSelectedRow();
    if (!row) return;
    row.event = value;
    renderEventsTable();
  }

  function cycleSelectedRowEvent() {
    const row = getSelectedRow();
    if (!row) return;

    const order = ["", "on", "off"];
    const currentIndex = order.indexOf(row.event);
    const nextIndex = currentIndex === -1 ? 0 : (currentIndex + 1) % order.length;

    row.event = order[nextIndex];
    renderEventsTable();
  }

  function focusAngleInputForSelectedRow() {
    const input = els.eventsTbody.querySelector(
      `input.angle-input[data-row-index="${state.selectedTableRowIndex}"]`
    );
    if (input) {
      input.focus();
      input.select();
    }
  }

  function copySelectedRow() {
    const row = getSelectedRow();
    if (!row) return;
    state.copiedRow = {
      event: row.event,
      angle: row.angle,
    };
  }

  function pasteToSelectedRow() {
    const row = getSelectedRow();
    if (!row || !state.copiedRow) return;

    row.event = state.copiedRow.event;
    row.angle = state.copiedRow.angle;
    renderEventsTable();
  }

  els.newRecipeBtn.addEventListener("click", addRecipe);
  els.copyRecipeBtn.addEventListener("click", copyRecipe);
  els.deleteRecipeBtn.addEventListener("click", deleteRecipe);

  els.newCycleBtn.addEventListener("click", addCycle);
  els.copyCycleBtn.addEventListener("click", copyCycle);
  els.deleteCycleBtn.addEventListener("click", deleteCycle);
  els.moveCycleUpBtn.addEventListener("click", () => moveCycle(-1));
  els.moveCycleDownBtn.addEventListener("click", () => moveCycle(1));

  els.clearCycleBtn.addEventListener("click", clearCycle);

  els.saveSettingsBtn.addEventListener("click", saveAll);
  els.backButton.addEventListener("click", goBack);

  els.recipeNameInput.addEventListener("change", saveRecipeMeta);
  els.recipeRepeatsInput.addEventListener("change", saveRecipeMeta);
  els.cycleTurnsInput.addEventListener("change", saveCycleMeta);

  document.addEventListener("keydown", (event) => {
    const target = event.target;
    const typing = isTypingContext(target);

    if (event.key === "F2") {
      event.preventDefault();
      goBack();
      return;
    }

    if (event.key === "F6") {
      event.preventDefault();
      saveAll();
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

    if (event.ctrlKey && event.key.toLowerCase() === "c") {
      event.preventDefault();
      copySelectedRow();
      return;
    }

    if (event.ctrlKey && event.key.toLowerCase() === "v") {
      event.preventDefault();
      pasteToSelectedRow();
      return;
    }

    if (event.key === "Insert") {
      event.preventDefault();

      if (document.activeElement === els.cycleList) {
        addCycle();
      } else {
        addRecipe();
      }
      return;
    }

    if (event.key === "Delete") {
      event.preventDefault();

      if (document.activeElement === els.cycleList) {
        deleteCycle();
      } else {
        deleteRecipe();
      }
      return;
    }

    if (event.ctrlKey && event.key === "ArrowUp") {
      event.preventDefault();
      moveCycle(-1);
      return;
    }

    if (event.ctrlKey && event.key === "ArrowDown") {
      event.preventDefault();
      moveCycle(1);
      return;
    }

    if (event.altKey && event.key === "ArrowUp") {
      event.preventDefault();
      selectRecipeByStep(-1);
      return;
    }

    if (event.altKey && event.key === "ArrowDown") {
      event.preventDefault();
      selectRecipeByStep(1);
      return;
    }

    if (event.key === "PageUp") {
      event.preventDefault();
      selectCycleByStep(-1);
      return;
    }

    if (event.key === "PageDown") {
      event.preventDefault();
      selectCycleByStep(1);
      return;
    }

    if (event.key === "ArrowUp") {
      event.preventDefault();
      selectTableRowByStep(-1);
      return;
    }

    if (event.key === "ArrowDown") {
      event.preventDefault();
      selectTableRowByStep(1);
      return;
    }

    if (event.key === " ") {
      event.preventDefault();
      cycleSelectedRowEvent();
      return;
    }

    if (event.key === "Enter") {
      event.preventDefault();
      focusAngleInputForSelectedRow();
      return;
    }

    if (event.key === "0") {
      event.preventDefault();
      setSelectedRowEvent("");
      return;
    }

    if (event.key === "1") {
      event.preventDefault();
      setSelectedRowEvent("on");
      return;
    }

    if (event.key === "2") {
      event.preventDefault();
      setSelectedRowEvent("off");
      return;
    }
  });

  loadRecipesFromBackend().catch((error) => {
    console.error(error);
    alert(`Ошибка загрузки рецептов: ${error.message}`);
  });
});