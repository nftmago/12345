import SwiftUI

struct AuthView: View {
    @EnvironmentObject var networkManager: NetworkManager
    @State private var isLoginMode = true
    @State private var username = ""
    @State private var email = ""
    @State private var password = ""
    @State private var confirmPassword = ""
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 30) {
                    // Logo and Title
                    VStack(spacing: 16) {
                        Image(systemName: "leaf.fill")
                            .font(.system(size: 60))
                            .foregroundColor(.green)
                        
                        Text("AINUT")
                            .font(.largeTitle)
                            .fontWeight(.bold)
                            .foregroundColor(.primary)
                        
                        Text("Your AI-Powered Nutrition Assistant")
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                            .multilineTextAlignment(.center)
                    }
                    .padding(.top, 40)
                    
                    // Auth Form
                    VStack(spacing: 20) {
                        // Username Field
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Username")
                                .font(.headline)
                                .foregroundColor(.primary)
                            
                            TextField("Enter username", text: $username)
                                .textFieldStyle(RoundedBorderTextFieldStyle())
                                .autocapitalization(.none)
                                .disableAutocorrection(true)
                        }
                        
                        // Email Field (Register only)
                        if !isLoginMode {
                            VStack(alignment: .leading, spacing: 8) {
                                Text("Email")
                                    .font(.headline)
                                    .foregroundColor(.primary)
                                
                                TextField("Enter email", text: $email)
                                    .textFieldStyle(RoundedBorderTextFieldStyle())
                                    .keyboardType(.emailAddress)
                                    .autocapitalization(.none)
                                    .disableAutocorrection(true)
                            }
                        }
                        
                        // Password Field
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Password")
                                .font(.headline)
                                .foregroundColor(.primary)
                            
                            SecureField("Enter password", text: $password)
                                .textFieldStyle(RoundedBorderTextFieldStyle())
                        }
                        
                        // Confirm Password Field (Register only)
                        if !isLoginMode {
                            VStack(alignment: .leading, spacing: 8) {
                                Text("Confirm Password")
                                    .font(.headline)
                                    .foregroundColor(.primary)
                                
                                SecureField("Confirm password", text: $confirmPassword)
                                    .textFieldStyle(RoundedBorderTextFieldStyle())
                            }
                        }
                        
                        // Error Message
                        if let errorMessage = networkManager.errorMessage {
                            Text(errorMessage)
                                .foregroundColor(.red)
                                .font(.caption)
                                .multilineTextAlignment(.center)
                        }
                        
                        // Submit Button
                        Button(action: {
                            Task {
                                if isLoginMode {
                                    await networkManager.login(username: username, password: password)
                                } else {
                                    if password == confirmPassword {
                                        await networkManager.register(username: username, email: email, password: password)
                                    } else {
                                        networkManager.errorMessage = "Passwords don't match"
                                    }
                                }
                            }
                        }) {
                            HStack {
                                if networkManager.isLoading {
                                    ProgressView()
                                        .scaleEffect(0.8)
                                        .foregroundColor(.white)
                                }
                                
                                Text(isLoginMode ? "Sign In" : "Create Account")
                                    .fontWeight(.semibold)
                            }
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(
                                LinearGradient(
                                    colors: [.green, .green.opacity(0.8)],
                                    startPoint: .leading,
                                    endPoint: .trailing
                                )
                            )
                            .foregroundColor(.white)
                            .cornerRadius(12)
                        }
                        .disabled(networkManager.isLoading || !isFormValid)
                        
                        // Toggle Auth Mode
                        Button(action: {
                            isLoginMode.toggle()
                            networkManager.errorMessage = nil
                        }) {
                            Text(isLoginMode ? "Don't have an account? Sign up" : "Already have an account? Sign in")
                                .font(.subheadline)
                                .foregroundColor(.green)
                        }
                    }
                    .padding(.horizontal, 20)
                    
                    Spacer()
                }
            }
            .navigationBarHidden(true)
        }
    }
    
    private var isFormValid: Bool {
        if isLoginMode {
            return !username.isEmpty && !password.isEmpty
        } else {
            return !username.isEmpty && !email.isEmpty && !password.isEmpty && !confirmPassword.isEmpty
        }
    }
}

#Preview {
    AuthView()
        .environmentObject(NetworkManager())
}