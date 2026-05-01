import NextAuth from "next-auth"
import type { NextAuthConfig } from "next-auth"

const config: NextAuthConfig = {
    providers: [
        {
            id: "casdoor",
            name: "Casdoor",
            type: "oauth",
            clientId: process.env.CASDOOR_CLIENT_ID!,
            clientSecret: process.env.CASDOOR_CLIENT_SECRET!,
            issuer: process.env.CASDOOR_ISSUER!,
            authorization: {
                url: `${process.env.CASDOOR_ISSUER}/login/oauth/authorize`,
                params: { scope: "openid profile email" },
            },
            token: {
                url: `${process.env.CASDOOR_ISSUER}/api/login/oauth/access_token`,
            },
            userinfo: {
                url: `${process.env.CASDOOR_ISSUER}/api/get-account`,
            },
            checks: ["pkce", "state"],
            profile(profile: any) {
                return {
                    id: profile.sub,
                    name: profile.name || profile.preferred_username,
                    email: profile.email,
                    image: profile.picture,
                }
            },
        },
    ],
    callbacks: {
        async jwt({ token, account, profile }) {
            // account 只在首次登录回调时存在，存入 accessToken
            if (account) {
                token.accessToken = account.access_token
                token.expiresAt = account.expires_at
            }
            if (profile) {
                token.sub = profile.sub ?? undefined
            }
            return token
        },
        async session({ session, token }) {
            session.accessToken = token.accessToken as string
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

export const { handlers, auth, signIn, signOut } = NextAuth(config)