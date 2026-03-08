let dayCount = 0

const saved = JSON.parse(localStorage.getItem("tripData"))

if(saved){
document.getElementById("tripName").value = saved.name || ""
document.getElementById("tripDates").value = saved.dates || ""
}

function saveTrip(){

const name = document.getElementById("tripName").value
const dates = document.getElementById("tripDates").value

localStorage.setItem("tripData",JSON.stringify({
name:name,
dates:dates
}))

}

function addDay(){

dayCount++

const container = document.getElementById("days")

const day = document.createElement("div")

day.className = "day"

day.innerHTML = `
<h3>Day ${dayCount}</h3>

<input id="activity-${dayCount}" placeholder="Activity">

<button onclick="addActivity(${dayCount})">
Add
</button>

<ul id="list-${dayCount}"></ul>
`

container.appendChild(day)

}

function addActivity(day){

const input = document.getElementById(`activity-${day}`)

if(input.value === "") return

const list = document.getElementById(`list-${day}`)

const li = document.createElement("li")

li.textContent = input.value

list.appendChild(li)

input.value = ""

}

const map = L.map('map').setView([20,0],2)

L.tileLayer(
'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
{
attribution:'© OpenStreetMap'
}
).addTo(map)

map.on("click",function(e){

const lat = e.latlng.lat
const lng = e.latlng.lng

const marker = L.marker([lat,lng]).addTo(map)

marker.bindPopup(
"Location<br>"+lat.toFixed(3)+","+lng.toFixed(3)
)

saveMarker(lat,lng)

})

function saveMarker(lat,lng){

let markers = JSON.parse(localStorage.getItem("markers")) || []

markers.push({lat:lat,lng:lng})

localStorage.setItem("markers",JSON.stringify(markers))

}

function loadMarkers(){

const markers = JSON.parse(localStorage.getItem("markers")) || []

markers.forEach(m=>{

L.marker([m.lat,m.lng]).addTo(map)

})

}

loadMarkers()

async function searchPlace(){

const query = document.getElementById("placeSearch").value

if(!query) return

const url = `https://nominatim.openstreetmap.org/search?format=json&q=${query}`

const res = await fetch(url)

const data = await res.json()

if(data.length === 0) return

const place = data[0]

const lat = parseFloat(place.lat)
const lon = parseFloat(place.lon)

map.setView([lat,lon],14)

const marker = L.marker([lat,lon]).addTo(map)

marker.bindPopup(place.display_name).openPopup()

saveMarker(lat,lon)

}

function exportPDF(){

const element = document.body

html2pdf()
.from(element)
.save("trip-itinerary.pdf")

}
