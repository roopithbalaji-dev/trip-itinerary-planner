let dayCount = 0;

function addDay() {

    dayCount++;

    const daysContainer = document.getElementById("days");

    const dayDiv = document.createElement("div");
    dayDiv.className = "day";

    dayDiv.innerHTML = `
        <h3>Day ${dayCount}</h3>
        <input id="activity-input-${dayCount}" placeholder="Add activity">
        <button onclick="addActivity(${dayCount})">Add Activity</button>
        <ul id="activity-list-${dayCount}"></ul>
    `;

    daysContainer.appendChild(dayDiv);

}

function addActivity(dayNumber){

    const input = document.getElementById(`activity-input-${dayNumber}`);
    const list = document.getElementById(`activity-list-${dayNumber}`);

    if(input.value.trim() === "") return;

    const li = document.createElement("li");
    li.textContent = input.value;

    list.appendChild(li);

    input.value = "";

}

