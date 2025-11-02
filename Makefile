# ============================================================================
# RTFM Discord Bot - Makefile
# ============================================================================
# Simple commands for current bot structure
# ============================================================================

.PHONY: help setup build up down restart logs clean

# Colors
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m

.DEFAULT_GOAL := help

# ============================================================================
# HELP
# ============================================================================

help: ## Show available commands
	@echo '${BLUE}RTFM Discord Bot - Available Commands${NC}'
	@echo ''
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "${GREEN}%-20s${NC} %s\n", $$1, $$2}'

# ============================================================================
# SETUP
# ============================================================================

setup: ## Initial setup (copy .env.example to .env)
	@echo "${BLUE}Setting up RTFM bot...${NC}"
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "${GREEN}.env file created!${NC}"; \
		echo "${YELLOW}Edit .env with your Discord token and Gemini API key${NC}"; \
	else \
		echo "${YELLOW}.env already exists${NC}"; \
	fi
	@mkdir -p discord_db logs
	@echo "${GREEN}Setup complete!${NC}"

check-env: ## Check if .env exists
	@if [ ! -f .env ]; then \
		echo "${YELLOW}No .env file found. Run 'make setup' first${NC}"; \
		exit 1; \
	fi

# ============================================================================
# DOCKER COMMANDS
# ============================================================================

build: check-env ## Build Docker image
	@echo "${BLUE}Building Docker image...${NC}"
	docker-compose build
	@echo "${GREEN}Build complete!${NC}"

up: check-env ## Start the bot
	@echo "${BLUE}Starting RTFM bot...${NC}"
	docker-compose up -d
	@echo "${GREEN}Bot started!${NC}"
	@echo "${YELLOW}Run 'make logs' to view logs${NC}"

down: ## Stop the bot
	@echo "${BLUE}Stopping bot...${NC}"
	docker-compose down
	@echo "${GREEN}Bot stopped!${NC}"

restart: ## Restart the bot
	@echo "${BLUE}Restarting bot...${NC}"
	docker-compose restart
	@echo "${GREEN}Bot restarted!${NC}"

# ============================================================================
# LOGS & MONITORING
# ============================================================================

logs: ## View bot logs (live)
	docker-compose logs -f bot

logs-processor: ## View message processor logs (live)
	docker-compose logs -f message-processor

logs-all: ## View all service logs (live)
	docker-compose logs -f

logs-tail: ## View last 100 log lines
	docker-compose logs --tail=100 bot

status: ## Show bot status
	docker-compose ps

# ============================================================================
# DEVELOPMENT
# ============================================================================

shell: ## Open shell in bot container
	docker-compose exec bot bash

rebuild: ## Rebuild and restart bot
	@echo "${BLUE}Rebuilding bot...${NC}"
	docker-compose down
	docker-compose build
	docker-compose up -d
	@echo "${GREEN}Bot rebuilt and restarted!${NC}"

# ============================================================================
# CLEANUP
# ============================================================================

clean: ## Remove containers and networks
	@echo "${YELLOW}Stopping and removing containers...${NC}"
	docker-compose down
	@echo "${GREEN}Cleanup complete!${NC}"

clean-all: ## Remove everything including database
	@echo "${YELLOW}WARNING: This will delete your message database!${NC}"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
		rm -rf discord_db/*; \
		echo "${GREEN}Everything cleaned!${NC}"; \
	fi

clean-logs: ## Remove log files
	rm -rf logs/*

# ============================================================================
# TESTING
# ============================================================================

test-connection: ## Test if bot can connect
	@echo "${BLUE}Testing bot connection...${NC}"
	@docker-compose logs bot | grep "Logged in as" && \
		echo "${GREEN}✓ Bot is connected!${NC}" || \
		echo "${YELLOW}Bot not connected yet. Check logs with 'make logs'${NC}"

test-kafka: ## Test Kafka integration
	@echo "${BLUE}Testing Kafka integration...${NC}"
	docker-compose exec message-processor python test_kafka.py --bootstrap-servers kafka:9092 --test all

init-topics: ## Initialize Kafka topics manually
	@echo "${BLUE}Initializing Kafka topics...${NC}"
	docker-compose exec message-processor python init_kafka_topics.py --bootstrap-servers kafka:9092 --action create

list-topics: ## List all Kafka topics
	@echo "${BLUE}Listing Kafka topics...${NC}"
	docker-compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list

# ============================================================================
# QUICK START
# ============================================================================

init: setup build up ## Complete initialization (setup + build + start)
	@echo "${GREEN}RTFM bot is ready!${NC}"
	@echo "${YELLOW}Check logs with: make logs${NC}"
