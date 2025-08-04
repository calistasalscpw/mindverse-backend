import mongoose, {Schema} from "mongoose";
import bcrypt from 'bcrypt';

const UserSchema = new Schema(
    {
        username: {
            type: String,
            required: true
        },
        email: {
            type: String,
            required: true,
            unique: true,
            match: [/.*@.*\..*/, "Please fill a valid email form"]
        },
        password: {
            type: String
        },
        isLead: {
            type: Boolean,
            default: false
        },
        isHR: {
            type: Boolean,
            default: false
        },
        registerType: {
            type: String,
            enum: ["normal", "google"],
            default: "normal"
        },
        profileImageUrl: String,
        socialId: String,
        // posts: [{type: mongoose.Schema.Types.ObjectId, ref: "Post"}],
        isVerified: {
            type: Boolean,
            default: false
        }
    }
)

UserSchema.pre("save", async function () {
    if (this.password && this.isNew || this.isModified("password")){
        this.password = await bcrypt.hash(this.password, 10)
    }
})

const User = mongoose.model("User", UserSchema);

export default User;