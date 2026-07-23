import { cookies } from "next/headers";

import { NotificationPreferencesForm } from "@/components/notification-preferences-form";
import { getNotificationPreferences, listNotifications } from "@/lib/product-api";

export default async function NotificationsPage() {
  const cookieHeader = (await cookies()).toString();
  const [preference, notifications] = await Promise.all([
    getNotificationPreferences(cookieHeader),
    listNotifications(cookieHeader),
  ]);

  return (
    <section className="page-stack">
      <div className="page-heading">
        <div><span className="eyebrow">Platform</span><h1>Notifications</h1></div>
        <span className="freshness">Durable portal evidence · in-app delivery</span>
      </div>
      <article className="panel form-panel">
        <div className="panel-heading"><div><span className="eyebrow">Preferences</span><h2>Notification sources</h2></div></div>
        <NotificationPreferencesForm preference={preference} />
      </article>
      <article className="panel">
        <div className="panel-heading"><div><span className="eyebrow">Inbox</span><h2>Recent notifications</h2></div></div>
        {notifications.length === 0 ? (
          <div className="empty-state"><strong>No notifications</strong><span>No enabled canonical event source currently has evidence for this actor.</span></div>
        ) : (
          <div className="table-wrap"><table>
            <thead><tr><th>Time</th><th>Category</th><th>Severity</th><th>Summary</th><th>Resource</th></tr></thead>
            <tbody>{notifications.map((notification) => <tr key={notification.notification_id}>
              <td>{new Date(notification.occurred_at).toLocaleString()}</td>
              <td>{notification.category}</td>
              <td>{notification.severity}</td>
              <td>{notification.summary}</td>
              <td>{notification.resource_type}:{notification.resource_id}</td>
            </tr>)}</tbody>
          </table></div>
        )}
      </article>
    </section>
  );
}
