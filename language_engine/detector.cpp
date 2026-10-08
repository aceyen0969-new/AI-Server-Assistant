#include <iostream>
#include <string>
#include <vector>
#include <cctype>

std::string normalize(
    const std::string& text
) {
    std::string result;

    for (char character : text) {
        if (std::isalnum(
                static_cast<unsigned char>(character)
            ) || character == '\'') {
            result += std::tolower(
                static_cast<unsigned char>(character)
            );
        } else {
            result += ' ';
        }
    }

    return result;
}

bool contains_word(
    const std::string& message,
    const std::string& word
) {
    std::string normalized_message = normalize(message);
    std::string normalized_word = normalize(word);

    std::size_t position = normalized_message.find(
        normalized_word
    );

    while (position != std::string::npos) {
        bool left_boundary =
            position == 0 ||
            normalized_message[position - 1] == ' ';

        std::size_t end_position =
            position + normalized_word.length();

        bool right_boundary =
            end_position == normalized_message.length() ||
            normalized_message[end_position] == ' ';

        if (left_boundary && right_boundary) {
            return true;
        }

        position = normalized_message.find(
            normalized_word,
            position + 1
        );
    }

    return false;
}

int main() {
    std::string message;

    std::cout << "Quasar Language Engine v0.3" << std::endl;
    std::cout << "Enter a message: ";

    std::getline(std::cin, message);

    std::vector<std::string> english_words = {
        "hello",
        "hi",
        "hey",
        "what",
        "why",
        "how",
        "the",
        "is",
        "are",
        "you",
        "your",
        "this",
        "that",
        "and",
        "but",
        "with"
    };

    std::vector<std::string> filipino_words = {
        "kamusta",
        "kumusta",
        "ako",
        "ikaw",
        "ang",
        "ng",
        "mga",
        "ito",
        "iyan",
        "iyon",
        "hindi",
        "oo",
        "bakit",
        "paano",
        "ano",
        "sino",
        "saan",
        "natin",
        "kayo",
        "kami"
    };

    int english_score = 0;
    int filipino_score = 0;

    for (const std::string& word : english_words) {
        if (contains_word(message, word)) {
            english_score++;
        }
    }

    for (const std::string& word : filipino_words) {
        if (contains_word(message, word)) {
            filipino_score++;
        }
    }

    std::string language = "unknown";
    bool mixed = false;
    double confidence = 0.0;

    if (english_score > 0 && filipino_score > 0) {
        language = "mixed";
        mixed = true;

        int total_score =
            english_score + filipino_score;

        confidence =
            static_cast<double>(total_score) / 4.0;

        if (confidence > 1.0) {
            confidence = 1.0;
        }
    }
    else if (english_score > filipino_score) {
        language = "english";

        confidence =
            static_cast<double>(english_score) / 3.0;

        if (confidence > 1.0) {
            confidence = 1.0;
        }
    }
    else if (filipino_score > english_score) {
        language = "filipino";

        confidence =
            static_cast<double>(filipino_score) / 3.0;

        if (confidence > 1.0) {
            confidence = 1.0;
        }
    }

    std::cout << std::endl;
    std::cout << "Message: " << message << std::endl;
    std::cout << "Language: " << language << std::endl;
    std::cout << "Mixed language: "
              << (mixed ? "true" : "false")
              << std::endl;
    std::cout << "English score: "
              << english_score
              << std::endl;
    std::cout << "Filipino score: "
              << filipino_score
              << std::endl;
    std::cout << "Confidence: "
              << confidence
              << std::endl;

    return 0;
}