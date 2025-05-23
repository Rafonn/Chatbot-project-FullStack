// app/api/presence/logout/logout.js
import { NextResponse } from "next/server";
import connectToSqlServer from "@/lib/db";

export async function POST(request) {
  try {
    const { userEmail } = await request.json();
    if (!userEmail) {
      return NextResponse.json({ error: "Faltou userEmail" }, { status: 400 });
    }

    const pool = await connectToSqlServer();
    await pool
      .request()
      .input("userEmail", userEmail)
      .query(`
        UPDATE ActiveUsers
        SET Active = 0
        WHERE UserEmail = @userEmail;
      `);

    return NextResponse.json({ ok: true });
  } catch (err) {
    console.error("Erro em /api/presence/logout:", err);
    return NextResponse.json({ error: "Erro interno" }, { status: 500 });
  }
}
