import { useEffect, useState } from "react";
import API from "../api";
import Layout from "../components/Layout";

export default function Emails() {

  const [emails, setEmails] = useState([]);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {

    try {

      const me = await API.get("/me");
      setUser(me.data);

      const res = await API.get("/emails");

      setEmails(res.data.data || []);

    } catch (err) {

      console.log(err);

    } finally {

      setLoading(false);

    }

  };

  useEffect(() => {
    load();
  }, []);

  const getTypeColor = (type) => {

    switch (type) {

      case "inventory":
        return "#dc2626";

      case "order":
        return "#2563eb";

      default:
        return "#7c3aed";

    }

  };

  return (

    <Layout user={user}>

      <div
        style={{
          padding: "30px",
          minHeight: "100vh",
          background:
            "linear-gradient(to bottom right, #f8fafc, #eef2ff)"
        }}
      >

        {/* HEADER */}

        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "30px",
            flexWrap: "wrap",
            gap: "20px"
          }}
        >

          <div>

            <h1
              style={{
                fontSize: "32px",
                marginBottom: "8px",
                color: "#111827"
              }}
            >
              📧 Email Simulation Center
            </h1>

            <p
              style={{
                color: "#6b7280",
                fontSize: "15px"
              }}
            >
              Monitor all simulated ERP email communications
            </p>

          </div>

          <div
            style={{
              background: "#fff",
              padding: "14px 22px",
              borderRadius: "16px",
              boxShadow:
                "0 10px 25px rgba(0,0,0,0.06)"
            }}
          >

            <h3
              style={{
                margin: 0,
                fontSize: "15px",
                color: "#6b7280"
              }}
            >
              Total Emails
            </h3>

            <h1
              style={{
                margin: 0,
                marginTop: "5px",
                color: "#111827"
              }}
            >
              {emails.length}
            </h1>

          </div>

        </div>


        {loading ? (

          <div
            style={{
              textAlign: "center",
              padding: "100px",
              fontSize: "20px",
              color: "#6b7280"
            }}
          >
            Loading emails...
          </div>

        ) : emails.length === 0 ? (

          <div
            style={{
              background: "#fff",
              padding: "60px",
              borderRadius: "24px",
              textAlign: "center",
              boxShadow:
                "0 10px 30px rgba(0,0,0,0.06)"
            }}
          >

            <h2
              style={{
                color: "#374151"
              }}
            >
              No Emails Found
            </h2>

            <p
              style={{
                color: "#6b7280"
              }}
            >
              Simulated emails will appear here.
            </p>

          </div>

        ) : (

          <div
            style={{
              display: "grid",
              gridTemplateColumns:
                "repeat(auto-fit,minmax(380px,1fr))",
              gap: "24px"
            }}
          >

            {emails.map((email) => (

              <div
                key={email.id}
                style={{
                  background: "#fff",
                  borderRadius: "24px",
                  padding: "24px",
                  boxShadow:
                    "0 12px 30px rgba(0,0,0,0.07)",
                  border:
                    "1px solid rgba(255,255,255,0.5)",
                  transition: "0.3s"
                }}
              >

                <div
                  style={{
                    display: "flex",
                    justifyContent:
                      "space-between",
                    alignItems: "center",
                    marginBottom: "20px"
                  }}
                >

                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "12px"
                    }}
                  >

                    <div
                      style={{
                        width: "55px",
                        height: "55px",
                        borderRadius: "16px",
                        background:
                          "linear-gradient(to bottom right,#2563eb,#7c3aed)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        color: "#fff",
                        fontSize: "24px"
                      }}
                    >
                      ✉️
                    </div>

                    <div>

                      <h3
                        style={{
                          margin: 0,
                          color: "#111827",
                          fontSize: "18px"
                        }}
                      >
                        {email.subject}
                      </h3>

                      <p
                        style={{
                          margin: 0,
                          color: "#6b7280",
                          fontSize: "13px"
                        }}
                      >
                        Simulated Email
                      </p>

                    </div>

                  </div>

                  <span
                    style={{
                      padding:
                        "8px 14px",
                      borderRadius: "999px",
                      background:
                        getTypeColor(
                          email.type
                        ),
                      color: "#fff",
                      fontSize: "12px",
                      fontWeight: "600",
                      textTransform:
                        "uppercase"
                    }}
                  >
                    {email.type}
                  </span>

                </div>

                {/* DETAILS */}

                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "14px"
                  }}
                >

                  <div>

                    <p
                      style={{
                        margin: 0,
                        fontSize: "13px",
                        color: "#9ca3af"
                      }}
                    >
                      Recipient
                    </p>

                    <h4
                      style={{
                        margin: 0,
                        marginTop: "4px",
                        color: "#111827"
                      }}
                    >
                      {email.to}
                    </h4>

                  </div>

                  <div>

                    <p
                      style={{
                        margin: 0,
                        fontSize: "13px",
                        color: "#9ca3af"
                      }}
                    >
                      Message
                    </p>

                    <div
                      style={{
                        marginTop: "8px",
                        background:
                          "#f9fafb",
                        padding: "16px",
                        borderRadius: "16px",
                        color: "#374151",
                        lineHeight: "1.6"
                      }}
                    >
                      {email.body}
                    </div>

                  </div>

                </div>

                {/* FOOTER */}

                <div
                  style={{
                    marginTop: "24px",
                    paddingTop: "18px",
                    borderTop:
                      "1px solid #e5e7eb",
                    display: "flex",
                    justifyContent:
                      "space-between",
                    alignItems: "center"
                  }}
                >

                  <div>

                    <p
                      style={{
                        margin: 0,
                        fontSize: "12px",
                        color: "#9ca3af"
                      }}
                    >
                      Delivery Status
                    </p>

                    <h4
                      style={{
                        margin: 0,
                        marginTop: "4px",
                        color: "#16a34a"
                      }}
                    >
                      ✅ Sent
                    </h4>

                  </div>

                  <small
                    style={{
                      color: "#6b7280",
                      textAlign: "right"
                    }}
                  >
                    {email.created_at}
                  </small>

                </div>

              </div>

            ))}

          </div>

        )}

      </div>

    </Layout>

  );

}
