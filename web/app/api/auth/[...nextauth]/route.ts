import NextAuth from "next-auth"
import type { NextAuthConfig } from "next-auth"

const config: NextAuthConfig = {
  providers: [
    {
      id: "casdoor",
      name: "Casdoor",
      type: "oauth",
      authorization: {
        url: "http://localhost:8000/login/oauth/authorize",
        params: { 
          scope: "openid profile email",
        } 
      },
      token: {
        url: "http://localhost:8000/api/login/oauth/access_token",
      },
      userinfo: {
        url: "http://localhost:8000/api/get-account",
      },
      checks: ["pkce", "state"],
      clientId: process.env.CASDOOR_CLIENT_ID!,
      clientSecret: process.env.CASDOOR_CLIENT_SECRET!,
      issuer: process.env.CASDOOR_ISSUER!,
      profile(profile: any) {
        return {
          id: profile.sub,
          name: profile.name || profile.preferred_username,
          email: profile.email,
          image: profile.picture,
        }
      },
    }
  ],
  callbacks: {
    async jwt({ token, account, profile }) {
      if (account) {
        token.accessToken = account.access_token
        token.refreshToken = account.refresh_token
        token.expiresAt = account.expires_at
      }
      if (profile) {
        token.sub = profile.sub
        token.name = profile.name
        token.email = profile.email
      }
      return token
    },
    async session({ session, token }) {
      session.accessToken = token.accessToken as string
      session.refreshToken = token.refreshToken as string
      session.user.id = token.sub as string
      return session
    },
  },
  pages: {
    signIn: "/",
  },
  session: {
    strategy: "jwt",
  },
}

const { handlers, auth, signIn, signOut } = NextAuth(config)
export { handlers, auth, signIn, signOut }
export const GET = handlers.GET
export const POST = handlers.POST
