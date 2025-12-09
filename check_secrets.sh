#!/bin/bash
# Скрипт проверки что секретные данные не попадут в Git

echo "🔍 Проверка безопасности перед публикацией на GitHub"
echo "=================================================="

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

errors=0

# Проверка 1: .env не должен быть в git
echo -e "\n📋 Проверка 1: Файл .env не отслеживается Git"
if git ls-files | grep -q "^.env$"; then
    echo -e "${RED}❌ ОШИБКА: .env находится в Git!${NC}"
    echo "   Выполните: git rm --cached .env"
    ((errors++))
else
    echo -e "${GREEN}✅ .env не отслеживается Git${NC}"
fi

# Проверка 2: .env игнорируется
echo -e "\n📋 Проверка 2: .env в .gitignore"
if git check-ignore -q .env; then
    echo -e "${GREEN}✅ .env правильно игнорируется${NC}"
else
    echo -e "${RED}❌ ОШИБКА: .env не в .gitignore!${NC}"
    ((errors++))
fi

# Проверка 3: Поиск секретных ключей в отслеживаемых файлах
echo -e "\n📋 Проверка 3: Поиск секретных ключей в коде"

# Паттерны для поиска
patterns=(
    "sk-proj-"  # OpenAI API keys
    "ck_[a-f0-9]{40}"  # WooCommerce Consumer Key
    "cs_[a-f0-9]{40}"  # WooCommerce Consumer Secret
    "[0-9]{10}:AA[A-Za-z0-9_-]{35}"  # Telegram Bot Token
)

found_secrets=0
for pattern in "${patterns[@]}"; do
    if git grep -q -E "$pattern" -- ':!.env' ':!.env.example'; then
        echo -e "${RED}❌ Найден возможный секретный ключ: $pattern${NC}"
        git grep -n -E "$pattern" -- ':!.env' ':!.env.example'
        ((found_secrets++))
        ((errors++))
    fi
done

if [ $found_secrets -eq 0 ]; then
    echo -e "${GREEN}✅ Секретные ключи не найдены в отслеживаемых файлах${NC}"
fi

# Проверка 4: .env.example не содержит реальных ключей
echo -e "\n📋 Проверка 4: .env.example содержит только примеры"
if grep -q "sk-proj-" .env.example || grep -q "ck_[a-f0-9]{40}" .env.example; then
    echo -e "${RED}❌ ВНИМАНИЕ: .env.example может содержать реальные ключи!${NC}"
    echo "   Замените их на примеры"
    ((errors++))
else
    echo -e "${GREEN}✅ .env.example содержит только примеры${NC}"
fi

# Проверка 5: Проверка staged файлов
echo -e "\n📋 Проверка 5: Файлы готовые к коммиту"
staged_files=$(git diff --cached --name-only)
if echo "$staged_files" | grep -q "^.env$"; then
    echo -e "${RED}❌ ОШИБКА: .env в staged файлах!${NC}"
    echo "   Выполните: git reset .env"
    ((errors++))
else
    echo -e "${GREEN}✅ .env не в staged файлах${NC}"
fi

# Итоги
echo -e "\n=================================================="
if [ $errors -eq 0 ]; then
    echo -e "${GREEN}✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!${NC}"
    echo -e "${GREEN}   Безопасно делать push на GitHub${NC}"
    exit 0
else
    echo -e "${RED}❌ НАЙДЕНО ОШИБОК: $errors${NC}"
    echo -e "${RED}   НЕ ДЕЛАЙТЕ push на GitHub!${NC}"
    echo -e "${YELLOW}   Исправьте ошибки и запустите проверку снова${NC}"
    exit 1
fi
