import passport from "passport";
import { Strategy as LocalStrategy } from "passport-local";
import { ExtractJwt, Strategy as JwtStrategy } from "passport-jwt";
import { Strategy as GoogleStrategy } from "passport-google-oauth2";
import bcrypt from "bcrypt";
import User from "../models/users.model.js";
import dotenv from 'dotenv';
dotenv.config()

const config = {
    usernameField: "email",
    passwordField: "password"
}

passport.use(
    new LocalStrategy(config, async function (email, password, done) {
        const user = await User.findOne({email})

        if(!user)
            return done(null, false, {message: "user not found"})

        const compareResult = await bcrypt.compare(password, user.password)
        if(!compareResult)
            return done(null, false, {message: "Invalid password"})

        return done(null, user)
    })
)

const jwtOption = {
    jwtFromRequest: ExtractJwt.fromExtractors([
        (req) => req.cookies.token || null
    ]),
    secretOrKey: process.env.JWT_SECRET_KEY
}

const backendUrl = process.env.BACKEND_URL || 'http://localhost:3000';

const googleOption = {
    clientID: process.env.GOOGLE_CLIENT_ID,
    clientSecret: process.env.GOOGLE_SECRET,
    callbackURL: `${backendUrl}/auth/login/google/callback`
}

passport.use(
    "jwt",
    new JwtStrategy(jwtOption, async (user, done) => {
        console.log('using passport.js JWT Strategy')
        const foundUser = await User.findById(user._id);
        if(!foundUser)
            return done(null, false, {message: "User not Found"})
        done(null, foundUser)
    })
)

passport.use(
    new GoogleStrategy(googleOption, async (assessToken, refeshToken, profile, done) => {
        try{
            const foundUser = await User.findOne({
                socialId: profile._json.sub,
                registerType: "google"
            })
            if(foundUser) {
                return done(null, foundUser)
            }
            const newUser = await User.create({
                email: profile._json.email,
                username: profile._json.name,
                socialId: profile._json.sub,
                registerType: "google"
            })

            return done(null, newUser)

        } catch (e) {
            return done(e)
        }
    })
)

export default passport;