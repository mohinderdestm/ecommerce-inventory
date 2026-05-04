import { useEffect, useState } from "react";

import API from "../api";

import Layout from "../components/Layout";

import {
  FaEnvelope,
  FaCheckCircle,
  FaBell
} from "react-icons/fa";

import "../styles/email.css";


export default function AdminEmailLogs() {

  const [emails, setEmails] = useState([]);

  const [user, setUser] = useState(null);


  const load = async () => {

    try {

      const me = await API.get("/me");

      setUser(me.data);

      const res = await API.get(
        "/admin/email-logs"
      );

      setEmails(res.data.data || []);

    } catch (err) {

      console.log(err);

    }

  };


  useEffect(() => {

    load();

  }, []);


  return (

    <Layout user={user}>

      <div className="email-page">

        {/* HEADER */}

        <div className="email-header">

          <div>

            <h1>
              <FaBell />
              System Email Logs
            </h1>

            <p>
              Monitor all admin-level
              email alerts and system
              communications
            </p>

          </div>

          <div className="email-stats">

            <h2>
              {emails.length}
            </h2>

            <span>
              Admin Emails
            </span>

          </div>

        </div>



        <div className="email-grid">

          {emails.map((email, index) => (

            <div
              key={index}
              className="email-card"
            >


              <div className="email-top">

                <div className="email-icon">

                  <FaEnvelope />

                </div>

                <div className="email-info">

                  <h3>
                    {email.subject}
                  </h3>

                  <p>
                    Admin Alert
                  </p>

                </div>

                <div className="email-badge">

                  SYSTEM

                </div>

              </div>



              <div className="email-body">

                <label>
                  Recipient
                </label>

                <h4>
                  {email.to}
                </h4>


                <label>
                  Message
                </label>

                <div className="email-message">

                  {email.message}

                </div>

              </div>

              <div className="email-footer">

                <div className="email-status">

                  <FaCheckCircle />

                  <span>
                    Delivered
                  </span>

                </div>

                <small>
                  {email.created_at}
                </small>

              </div>

            </div>

          ))}

        </div>

      </div>

    </Layout>

  );

}