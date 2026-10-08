#include <iostream>
#include <string>
#include <vector>

bool contains_word(
    const std::string& message,
    const std::string& word
) {
    return message.find(word) != std::string::npos;
}

int main() {
    std::string message;

    std::cout << "Quasar Language Engine v0.2" << std::endl;
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

        int total_score = english_score + filipino_score;
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