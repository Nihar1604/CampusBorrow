import React, { useEffect, useState } from "react";
import "./App.css";

const BASE_URL = window.location.hostname.includes("localhost")
  ? "http://127.0.0.1:5000"
  : window.location.origin;


function App() {
  const [view, setView] = useState("login"); // login, register, booking
  const [token, setToken] = useState(localStorage.getItem("accessToken") || "");
  const [slots, setSlots] = useState([]);
  const [booking, setBooking] = useState(null);

  const [loginInfo, setLoginInfo] = useState({ username: "", password: "" });
  const [registerInfo, setRegisterInfo] = useState({ username: "", name: "", email: "", phone: "", password: "" });

  useEffect(() => {
    if (!token) return;

    setView("booking");

    const fetchSlots = async () => {
      const res = await fetch(`${BASE_URL}/api/slots`);
      const data = await res.json();
      setSlots(data.slots.filter(s => s.status === "available"));
    };

    const fetchBooking = async () => {
      const res = await fetch(`${BASE_URL}/api/me`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      setBooking(data.booking || null);
    };

    fetchSlots();
    fetchBooking();
  }, [token]);

  const handleLogin = async () => {
    const res = await fetch(`${BASE_URL}/api/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(loginInfo),
    });
    const data = await res.json();
    if (res.ok) {
      localStorage.setItem("accessToken", data.access_token);
      setToken(data.access_token);
    } else {
      alert(data.error || "Login failed");
    }
  };

  const handleRegister = async () => {
    const res = await fetch(`${BASE_URL}/api/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(registerInfo),
    });
    const data = await res.json();
    if (res.ok) {
      setView("login");
    } else {
      alert(data.error || "Registration failed");
    }
  };

  const handleBook = async (slotId) => {
    const res = await fetch(`${BASE_URL}/api/book`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ slot_id: slotId }),
    });
    const data = await res.json();
    if (res.ok) {
      alert("Slot booked!");
      setSlots(prev => prev.filter(s => s.id !== slotId));
      setBooking(data.booking);
    } else {
      alert(data.error || "Booking failed");
    }
  };

  const handleCancel = async () => {
    const res = await fetch(`${BASE_URL}/api/cancel`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = await res.json();
    if (res.ok) {
      alert("Booking cancelled");
      setBooking(null);
      // refresh slots
      const res = await fetch(`${BASE_URL}/api/slots`);
      const data = await res.json();
      setSlots(data.slots.filter(s => s.status === "available"));
    } else {
      alert(data.error || "Cancellation failed");
    }
  };

  const handleLogout = () => {
    setToken("");
    localStorage.removeItem("accessToken");
    setView("login");
    setBooking(null);
    setSlots([]);
  };

  return (
    <div className="App">
      <h1>Meeting Booking</h1>

      {view === "login" && (
        <div>
          <input placeholder="Username" onChange={e => setLoginInfo({ ...loginInfo, username: e.target.value })} />
          <input type="password" placeholder="Password" onChange={e => setLoginInfo({ ...loginInfo, password: e.target.value })} />
          <button onClick={handleLogin}>Login</button>
          <button onClick={() => setView("register")}>Register</button>
        </div>
      )}

      {view === "register" && (
        <div>
          <input placeholder="Username" onChange={e => setRegisterInfo({ ...registerInfo, username: e.target.value })} />
          <input placeholder="Full Name" onChange={e => setRegisterInfo({ ...registerInfo, name: e.target.value })} />
          <input placeholder="Email" onChange={e => setRegisterInfo({ ...registerInfo, email: e.target.value })} />
          <input placeholder="Phone" onChange={e => setRegisterInfo({ ...registerInfo, phone: e.target.value })} />
          <input type="password" placeholder="Password" onChange={e => setRegisterInfo({ ...registerInfo, password: e.target.value })} />
          <button onClick={handleRegister}>Submit</button>
          <button onClick={() => setView("login")}>Back to Login</button>
        </div>
      )}

      {view === "booking" && (
        <div>
          <button onClick={handleLogout}>Logout</button>
          <h2>Available Slots</h2>
          <ul>
            {slots.map(slot => (
              <li key={slot.id}>
                {slot.datetime} <button onClick={() => handleBook(slot.id)}>Book</button>
              </li>
            ))}
          </ul>

          <h3>Your Booking</h3>
          {booking ? (
            <div>
              {booking.datetime}
              <button onClick={handleCancel}>Cancel</button>
            </div>
          ) : (
            <p>No active booking</p>
          )}
        </div>
      )}
    </div>
  );
}

export default App;
