# Logs Directory

This directory stores various types of log files for the chess application.

## Log Types

### 1. Game Logs
- **File Pattern**: `game_YYYYMMDD.log`
- **Content**: Game session information, errors, AI move calculations
- **Rotation**: Daily rotation

### 2. AI Training Logs  
- **File Pattern**: `training_YYYYMMDD.log`
- **Content**: Training progress, model performance metrics
- **Rotation**: Per training session

### 3. Debug Logs
- **File Pattern**: `debug_YYYYMMDD.log`
- **Content**: Detailed debugging information for development
- **Rotation**: Daily rotation

### 4. Performance Logs
- **File Pattern**: `performance_YYYYMMDD.log`
- **Content**: Performance metrics, response times, resource usage
- **Rotation**: Daily rotation

## Log Levels

- **DEBUG**: Detailed information for debugging
- **INFO**: General operational information
- **WARNING**: Warning messages about potential issues
- **ERROR**: Error messages for handled exceptions
- **CRITICAL**: Critical errors that may cause application failure

## Configuration

Log settings can be configured in `config/settings.py`:
- Log levels
- File rotation settings
- Output formats
- Console output options
