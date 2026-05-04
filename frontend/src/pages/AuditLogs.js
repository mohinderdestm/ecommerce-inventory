import { useEffect, useState } from "react";
import API from "../api";
import Layout from "../components/Layout";

export default function AuditLogs() {

  const [logs, setLogs] = useState([]);
  const [user, setUser] = useState(null);

  useEffect(() => {
    load();
  }, []);

  const load = async () => {

    try {

      const me = await API.get("/me");

      setUser(me.data);

      const res = await API.get("/audit-logs");

      setLogs(res.data);

    } catch (err) {

      console.error(err);

    }

  };

  return (

    <Layout user={user}>

      <div className="card">

        <h2>Audit Logs</h2>

        <table
          style={{
            width: "100%",
            marginTop: "20px",
            borderCollapse: "collapse"
          }}
        >

          <thead>

            <tr
              style={{
                background: "#f3f4f6"
              }}
            >

              <th style={th}>Time</th>
              <th style={th}>User</th>
              <th style={th}>Role</th>
              <th style={th}>Action</th>
              <th style={th}>Details</th>

            </tr>

          </thead>

          <tbody>

            {logs.map((log) => (

              <tr
                key={log.id}
                style={{
                  borderBottom:
                    "1px solid #ddd"
                }}
              >

                <td style={td}>
                  {log.time}
                </td>

                <td style={td}>
                  {log.user}
                </td>

                <td style={td}>
                  {log.role}
                </td>

                <td style={td}>
                  {log.action}
                </td>

                <td style={td}>
                  {log.message}
                </td>

              </tr>

            ))}

          </tbody>

        </table>

      </div>

    </Layout>

  );

}

const th = {

  padding: "14px",
  textAlign: "left",
  fontWeight: "bold"

};

const td = {

  padding: "14px",
  textAlign: "left"

};