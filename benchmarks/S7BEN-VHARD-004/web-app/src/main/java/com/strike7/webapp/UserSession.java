package com.strike7.webapp;

import java.io.Serializable;

public class UserSession implements Serializable {
    private static final long serialVersionUID = 1L;

    private String username;
    private String role;
    private boolean isAdmin;

    public UserSession(String username, String role, boolean isAdmin) {
        this.username = username;
        this.role = role;
        this.isAdmin = isAdmin;
    }

    public String getUsername() {
        return username;
    }

    public void setUsername(String username) {
        this.username = username;
    }

    public String getRole() {
        return role;
    }

    public void setRole(String role) {
        this.role = role;
    }

    public boolean isAdmin() {
        return isAdmin;
    }

    public void setAdmin(boolean admin) {
        isAdmin = admin;
    }
}
