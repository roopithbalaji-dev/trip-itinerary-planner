let dayCount = 0;

function addDay() {

    dayCount++;

    const daysContainer = document.getElementById("days");

    const dayDiv = document.createElement("div");
    dayDiv.className = "day";

    dayDiv.innerHTML = `
        <h3>Day ${dayCount}</h3>
        <input placeholder="Add activity">
        <button>Add</button>
    `;

    daysContainer.appendChild(dayDiv);

}
