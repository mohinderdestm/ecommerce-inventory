import { useEffect, useState } from "react";
import API from "../api";
import Layout from "../components/Layout";

export default function Notifications() {

  const [notifications, setNotifications] = useState([]);
  const [user, setUser] = useState(null);

  const load = async () => {

    try {

      const me = await API.get("/me");
      setUser(me.data);

      const res = await API.get("/notifications");

      setNotifications(res.data.data || []);

    } catch (err) {
      console.log(err);
    }
};
 useEffect(() => {
    load();
  }, []);

  const markRead = async (id) => {

    try {

      await API.put(`/notifications/${id}/read`);

      load();

    } catch {
      alert("Failed");
    }
  };

   return (
    <Layout user={user}>

      <div className="page">

        <h2>Notifications</h2>

        <div className="grid">

          {notifications.map(n => (

            <div
              key={n.id}
              className="card"
              style={{
                border: n.read
                  ? "1px solid #ddd"
                  : "2px solid #2563eb"
              }}
            >

              <h3>{n.title}</h3>
                <p>{n.message}</p>

              <small>
                {n.created_at}
              </small>

              {!n.read && (
                <button
                  className="primary"
                  onClick={() => markRead(n.id)}
                >
                  Mark as Read
                </button>
              )}

            </div>
          ))}

        </div>

      </div>

    </Layout>
  );
}