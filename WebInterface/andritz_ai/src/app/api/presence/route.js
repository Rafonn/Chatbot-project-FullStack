// app/api/presence/route.ts
import { NextResponse } from "next/server";
import connectToSqlServer from "@/lib/db";

export async function POST(request) {
  try {
    const { userEmail } = await request.json();
    if (!userEmail) {
      return NextResponse.json({ error: "Faltou userEmail" }, { status: 400 });
    }

    const pool = await connectToSqlServer();
    const now = new Date();

    const updateResult = await pool
      .request()
      .input("userEmail", userEmail)
      .input("now", now)
      .query(`
        UPDATE ActiveUsers
        SET LastActive = @now,
            Active     = 1
        WHERE UserEmail = @userEmail;
      `);

    if (updateResult.rowsAffected[0] === 0) {
      await pool
        .request()
        .input("userEmail", userEmail)
        .input("now", now)
        .query(`
          INSERT INTO ActiveUsers (UserEmail, LastActive, Active)
          VALUES (@userEmail, @now, 1);
        `);
    }

    return NextResponse.json({ ok: true });
  } catch (err) {
    console.error("Erro em /api/presence (heartbeat):", err);
    return NextResponse.json({ error: "Erro interno" }, { status: 500 });
  }
}
