<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'

interface Device {
    id: number
    name: string
}

const devices = ref<Device[]>([])
const selectedDevice = ref<number | null>(null)
const showModal = ref(false)
const reservationDetails = ref({
    input: '{\n  "additionalProp1": {}\n}', // base valid JSON
    output: '{\n  "additionalProp1": {}\n}', // base valid JSON
    simulation_time: 0,
    sampling_rate: 0,
    note: '',
    device_id: null as number | null,
    experiment_id: 1, // dummy for now
    schema_id: 1, // dummy for now
})

onMounted(async () => {
    const response = await fetch('http://localhost:8000/api/device/')
    if (response.ok) {
        devices.value = await response.json()
    }
})

// Show modal when device is selected
watch(selectedDevice, (newVal) => {
    if (newVal) {
        showModal.value = true
        reservationDetails.value.device_id = newVal
    }
})

const submitReservation = async () => {
    let inputJson, outputJson
    try {
        inputJson = reservationDetails.value.input ? JSON.parse(reservationDetails.value.input) : {}
        outputJson = reservationDetails.value.output
            ? JSON.parse(reservationDetails.value.output)
            : {}
    } catch (e) {
        alert('Input or Output is not valid JSON!')
        return
    }
    const payload = {
        ...reservationDetails.value,
        input: inputJson,
        output: outputJson,
    }
    console.log('Payload:', payload) // <-- Add this line
    const response = await fetch('http://localhost:8000/api/reserved_experiment/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    })
}
</script>

<template>
    <div class="card bg-base-300!">
        <h2>Reservations</h2>
        <!-- Device Dropdown -->
        <label for="device">Select Device:</label>
        <select v-model="selectedDevice" id="device" class="styled-dropdown bg-base-100!">
            <option disabled value="">-- Choose a device --</option>
            <option v-for="device in devices" :key="device.id" :value="device.id">
                {{ device.name }}
            </option>
        </select>
        <!-- Modal for reservation details -->
        <div v-if="showModal" class="modal">
            <h3>Reservation Details</h3>
            <label>Input (JSON):</label>
            <textarea v-model="reservationDetails.input" rows="3" />
            <label>Output (JSON):</label>
            <textarea v-model="reservationDetails.output" rows="3" />
            <label>Simulation Time:</label>
            <input v-model="reservationDetails.simulation_time" type="number" />
            <label>Sampling Rate:</label>
            <input v-model="reservationDetails.sampling_rate" type="number" />
            <label>Note:</label>
            <input v-model="reservationDetails.note" type="text" />
            <button @click="submitReservation">Reserve</button>
            <button @click="((showModal = false), (selectedDevice = null))">Cancel</button>
        </div>
    </div>
</template>

<style scoped>
.modal textarea {
    padding: 0.5rem 1rem;
    border-radius: 6px;
    border: 1px solid #94a3b8;
    background: #fff;
    color: #1e293b;
    font-size: 1rem;
    margin-bottom: 0.5rem;
    outline: none;
    transition: border-color 0.2s;
    resize: vertical;
}
.modal {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: #f9fafb;
    border: 1px solid #94a3b8;
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(30, 41, 59, 0.15);
    padding: 2rem 2.5rem;
    z-index: 1000;
    min-width: 320px;
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.modal h3 {
    margin-top: 0;
    margin-bottom: 0.5rem;
    color: #1e293b;
    font-size: 1.25rem;
    font-weight: 600;
}

.modal label {
    font-size: 0.95rem;
    color: #374151;
    margin-bottom: 0.25rem;
}

.modal input[type='number'],
.modal input[type='string'],
.modal input[type='text'] {
    padding: 0.5rem 1rem;
    border-radius: 6px;
    border: 1px solid #94a3b8;
    background: #fff;
    color: #1e293b;
    font-size: 1rem;
    margin-bottom: 0.5rem;
    outline: none;
    transition: border-color 0.2s;
}

.modal input:focus {
    border-color: #3b82f6;
}

.modal button {
    padding: 0.5rem 1.5rem;
    border-radius: 6px;
    border: none;
    font-size: 1rem;
    font-weight: 500;
    cursor: pointer;
    margin-right: 0.5rem;
    transition:
        background 0.2s,
        color 0.2s;
}

.modal button:first-of-type {
    background: #3b82f6;
    color: #fff;
}

.modal button:first-of-type:hover {
    background: #2563eb;
}

.modal button:last-of-type {
    background: #e5e7eb;
    color: #374151;
}

.modal button:last-of-type:hover {
    background: #cbd5e1;
}

.styled-dropdown {
    padding: 0.5rem 1rem;
    border-radius: 6px;
    border: 1px solid #94a3b8;
    background: #f1f5f9;
    color: #1e293b;
    font-size: 1rem;
    margin-bottom: 1rem;
    outline: none;
    transition: border-color 0.2s;
}
.styled-dropdown:focus {
    border-color: #3b82f6;
}
</style>
