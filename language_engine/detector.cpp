#include <iostream>
#include <string>
#include <vector>
#include <cctype>
#include <algorithm>
#include <map>
#include <fstream>

std::string normalize(
    const std::string& text
) {
    std::string result;

    for (char character : text) {
        if (
            std::isalnum(
                static_cast<unsigned char>(character)
            ) ||
            character == '\''
        ) {
            result += std::tolower(
                static_cast<unsigned char>(character)
            );
        } else {
            result += ' ';
        }
    }

    return result;
}

std::map<std::string, int> build_trigrams(
    const std::string& text
) {
    std::map<std::string, int> trigrams;

    std::string normalized =
        normalize(text);

    for (
        std::size_t i = 0;
        i + 2 < normalized.length();
        i++
    ) {
        if (
            normalized[i] == ' ' ||
            normalized[i + 1] == ' ' ||
            normalized[i + 2] == ' '
        ) {
            continue;
        }

        std::string trigram =
            normalized.substr(i, 3);

        trigrams[trigram]++;
    }

    return trigrams;
}

std::map<std::string, int> build_profile(
    const std::string& filename
) {
    std::map<std::string, int> profile;

    std::ifstream file(filename);

    if (!file.is_open()) {
        std::cerr
            << "Failed to open training file: "
            << filename
            << std::endl;

        return profile;
    }

    std::string line;

    while (std::getline(file, line)) {

        std::map<std::string, int> trigrams =
            build_trigrams(line);

        for (
            const auto& entry :
            trigrams
        ) {
            profile[entry.first] +=
                entry.second;
        }
    }

    file.close();

    return profile;
}

std::map<std::string, double> normalize_profile(
    const std::map<std::string, int>& profile
) {
    std::map<std::string, double> normalized;

    int total = 0;

    for (
        const auto& entry :
        profile
    ) {
        total += entry.second;
    }

    if (total == 0) {
        return normalized;
    }

    for (
        const auto& entry :
        profile
    ) {
        normalized[entry.first] =
            static_cast<double>(
                entry.second
            ) /
            static_cast<double>(
                total
            );
    }

    return normalized;
}

bool contains_word(
    const std::string& message,
    const std::string& word
) {
    std::string normalized_message =
        normalize(message);

    std::string normalized_word =
        normalize(word);

    std::size_t position =
        normalized_message.find(
            normalized_word
        );

    while (
        position != std::string::npos
    ) {
        bool left_boundary =
            position == 0 ||
            normalized_message[position - 1] == ' ';

        std::size_t end_position =
            position + normalized_word.length();

        bool right_boundary =
            end_position ==
                normalized_message.length() ||
            normalized_message[end_position] == ' ';

        if (
            left_boundary &&
            right_boundary
        ) {
            return true;
        }

        position =
            normalized_message.find(
                normalized_word,
                position + 1
            );
    }

    return false;
}

double calculate_trigram_score(
    const std::map<std::string, int>& trigrams,
    const std::map<std::string, double>& profile
) {
    double score = 0.0;

    for (
        const auto& pattern :
        profile
    ) {
        auto found =
            trigrams.find(
                pattern.first
            );

        if (
            found != trigrams.end()
        ) {
            score +=
                found->second *
                pattern.second;
        }
    }

    return score;
}

int main() {

    std::cout
        << "Quasar Language Engine v0.6.2"
        << std::endl;

    std::map<std::string, int> english_raw =
        build_profile(
            "training/english.txt"
        );

    std::map<std::string, int> filipino_raw =
        build_profile(
            "training/filipino.txt"
        );

    std::map<std::string, int> bisaya_raw =
        build_profile(
            "training/bisaya.txt"
        );

    std::map<std::string, double> english_trigrams =
        normalize_profile(
            english_raw
        );

    std::map<std::string, double> filipino_trigrams =
        normalize_profile(
            filipino_raw
        );

    std::map<std::string, double> bisaya_trigrams =
        normalize_profile(
            bisaya_raw
        );

    std::cout
        << "English trigrams: "
        << english_trigrams.size()
        << std::endl;

    std::cout
        << "Filipino trigrams: "
        << filipino_trigrams.size()
        << std::endl;

    std::cout
        << "Bisaya trigrams: "
        << bisaya_trigrams.size()
        << std::endl;

    std::string message;

    std::cout
        << "Enter a message: ";

    std::getline(
        std::cin,
        message
    );

    std::map<std::string, int> trigrams =
        build_trigrams(
            message
        );

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

    std::vector<std::string> bisaya_words = {
        "unsa",
        "ngano",
        "kinsa",
        "asa",
        "kanus-a",
        "kumusta",
        "ako",
        "ikaw",
        "imo",
        "imong",
        "atong",
        "nato",
        "sila",
        "niya",
        "wala",
        "dili",
        "oo",
        "mao",
        "naa",
        "gihimo",
        "buhat",
        "buhaton",
        "adto",
        "ari",
        "dinhi",
        "didto",
        "unsaon",
        "nganong"
    };

    int english_word_score = 0;
    int filipino_word_score = 0;
    int bisaya_word_score = 0;

    for (
        const std::string& word :
        english_words
    ) {
        if (
            contains_word(
                message,
                word
            )
        ) {
            english_word_score++;
        }
    }

    for (
        const std::string& word :
        filipino_words
    ) {
        if (
            contains_word(
                message,
                word
            )
        ) {
            filipino_word_score++;
        }
    }

    for (
        const std::string& word :
        bisaya_words
    ) {
        if (
            contains_word(
                message,
                word
            )
        ) {
            bisaya_word_score++;
        }
    }

    double english_trigram_score =
        calculate_trigram_score(
            trigrams,
            english_trigrams
        );

    double filipino_trigram_score =
        calculate_trigram_score(
            trigrams,
            filipino_trigrams
        );

    double bisaya_trigram_score =
        calculate_trigram_score(
            trigrams,
            bisaya_trigrams
        );

    double english_score =
        english_word_score +
        english_trigram_score;

    double filipino_score =
        filipino_word_score +
        filipino_trigram_score;

    double bisaya_score =
        bisaya_word_score +
        bisaya_trigram_score;

    double highest_score =
        std::max({
            english_score,
            filipino_score,
            bisaya_score
        });

    int strong_language_count = 0;

    if (
        english_word_score > 0
    ) {
        strong_language_count++;
    }

    if (
        filipino_word_score > 0
    ) {
        strong_language_count++;
    }

    if (
        bisaya_word_score > 0
    ) {
        strong_language_count++;
    }

    std::string language =
        "unknown";

    bool mixed = false;

    double confidence = 0.0;

    if (
        strong_language_count >= 2
    ) {
        language = "mixed";
        mixed = true;
    }
    else if (
        highest_score > 0
    ) {
        if (
            english_score ==
            highest_score
        ) {
            language = "english";
        }
        else if (
            filipino_score ==
            highest_score
        ) {
            language = "filipino";
        }
        else {
            language = "bisaya";
        }
    }

    double total_score =
        english_score +
        filipino_score +
        bisaya_score;

    if (
        total_score > 0
    ) {
        confidence =
            highest_score /
            total_score;
    }

    std::cout
        << "{"
        << "\"language\":\""
        << language
        << "\","
        << "\"mixed\":"
        << (
            mixed
                ? "true"
                : "false"
        )
        << ","
        << "\"confidence\":"
        << confidence
        << ","
        << "\"english_word_score\":"
        << english_word_score
        << ","
        << "\"filipino_word_score\":"
        << filipino_word_score
        << ","
        << "\"bisaya_word_score\":"
        << bisaya_word_score
        << ","
        << "\"english_trigram_score\":"
        << english_trigram_score
        << ","
        << "\"filipino_trigram_score\":"
        << filipino_trigram_score
        << ","
        << "\"bisaya_trigram_score\":"
        << bisaya_trigram_score
        << "}"
        << std::endl;

    return 0;
}