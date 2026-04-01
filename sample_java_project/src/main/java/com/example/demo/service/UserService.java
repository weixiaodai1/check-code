package com.example.demo.service;

import com.example.demo.model.User;
import com.example.demo.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;

/**
 * User Service with Spring features
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class UserService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    /**
     * Get all users with caching
     */
    @Cacheable(value = "users")
    @Transactional(readOnly = true)
    public List<User> getAllUsers() {
        log.info("Fetching all users from database");
        return userRepository.findAll();
    }

    /**
     * Find user by username
     */
    @Transactional(readOnly = true)
    public Optional<User> findByUsername(String username) {
        return userRepository.findByUsernameWithRoles(username);
    }

    /**
     * Create new user
     */
    @CacheEvict(value = "users", allEntries = true)
    @Transactional
    public User createUser(User user) {
        log.info("Creating new user: {}", user.getUsername());

        // Encode password
        user.setPassword(passwordEncoder.encode(user.getPassword()));

        return userRepository.save(user);
    }

    /**
     * Update existing user
     */
    @CacheEvict(value = "users", allEntries = true)
    @Transactional
    public User updateUser(Long id, User userDetails) {
        User user = userRepository.findById(id)
            .orElseThrow(() -> new RuntimeException("User not found"));

        user.setEmail(userDetails.getEmail());
        user.setUsername(userDetails.getUsername());

        if (userDetails.getPassword() != null && !userDetails.getPassword().isEmpty()) {
            user.setPassword(passwordEncoder.encode(userDetails.getPassword()));
        }

        return userRepository.save(user);
    }

    /**
     * Delete user
     */
    @CacheEvict(value = "users", allEntries = true)
    @Transactional
    public void deleteUser(Long id) {
        userRepository.deleteById(id);
    }
}
