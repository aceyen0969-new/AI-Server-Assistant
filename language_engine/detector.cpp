#include <iostream>
#include <string>
#include <sstream>
#include <vector>
#include <map>
#include <fstream>
#include <set>
#include <algorithm>
#include <cctype>

struct LanguageSegment {
    std::string language;
    std::vector<std::string> words;
};

std::string normalize(
    const std::string& text
) {
    std::string result;

    for (char c : text) {
        if (
            std::isalnum(
                static_cast<unsigned char>(c)
            )
        ) {
            result += static_cast<char>(
                std::tolower(
                    static_cast<unsigned char>(c)
                )
            );
        }
        else {
            result += ' ';
        }
    }

    return result;
}

std::vector<std::string> tokenize(
    const std::string& text
) {
    std::vector<std::string> words;

    std::stringstream stream(
        normalize(text)
    );

    std::string word;

    while (stream >> word) {
        words.push_back(word);
    }

    return words;
}

std::vector<std::string> build_trigrams(
    const std::string& text
) {
    std::vector<std::string> trigrams;

    std::string normalized =
        normalize(text);

    for (
        std::size_t i = 0;
        i + 2 < normalized.size();
        ++i
    ) {
        if (
            normalized[i] == ' ' ||
            normalized[i + 1] == ' ' ||
            normalized[i + 2] == ' '
        ) {
            continue;
        }

        trigrams.push_back(
            normalized.substr(i, 3)
        );
    }

    return trigrams;
}

std::map<std::string, int> build_profile(
    const std::string& filename
) {
    std::map<std::string, int> profile;

    std::ifstream file(
        filename
    );

    if (!file.is_open()) {
        std::cerr
            << "Could not open training file: "
            << filename
            << std::endl;

        return profile;
    }

    std::string line;

    while (std::getline(file, line)) {
        std::vector<std::string> trigrams =
            build_trigrams(line);

        for (
            const std::string& trigram :
            trigrams
        ) {
            profile[trigram]++;
        }
    }

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
            ) / total;
    }

    return normalized;
}

std::set<std::string> build_vocabulary(
    const std::string& filename
) {
    std::set<std::string> vocabulary;

    std::ifstream file(
        filename
    );

    if (!file.is_open()) {
        std::cerr
            << "Could not open training file: "
            << filename
            << std::endl;

        return vocabulary;
    }

    std::string line;

    while (std::getline(file, line)) {
        std::vector<std::string> words =
            tokenize(line);

        for (
            const std::string& word :
            words
        ) {
            if (!word.empty()) {
                vocabulary.insert(word);
            }
        }
    }

    return vocabulary;
}

int count_vocabulary_matches(
    const std::vector<std::string>& words,
    const std::set<std::string>& vocabulary
) {
    int score = 0;

    for (
        const std::string& word :
        words
    ) {
        if (
            vocabulary.find(word)
            != vocabulary.end()
        ) {
            score++;
        }
    }

    return score;
}

int count_unique_vocabulary_matches(
    const std::vector<std::string>& words,
    const std::set<std::string>& vocabulary,
    const std::set<std::string>& other_vocabulary_1,
    const std::set<std::string>& other_vocabulary_2
) {
    int score = 0;

    for (
        const std::string& word :
        words
    ) {
        if (
            vocabulary.find(word)
            != vocabulary.end() &&
            other_vocabulary_1.find(word)
                == other_vocabulary_1.end() &&
            other_vocabulary_2.find(word)
                == other_vocabulary_2.end()
        ) {
            score++;
        }
    }

    return score;
}

double calculate_trigram_score(
    const std::vector<std::string>& trigrams,
    const std::map<std::string, double>& profile
) {
    if (trigrams.empty()) {
        return 0.0;
    }

    double score = 0.0;

    for (
        const std::string& trigram :
        trigrams
    ) {
        auto found =
            profile.find(trigram);

        if (
            found != profile.end()
        ) {
            score += found->second;
        }
    }

    return score;
}

double calculate_score_margin(
    double english_score,
    double filipino_score,
    double bisaya_score
) {
    std::vector<double> scores = {
        english_score,
        filipino_score,
        bisaya_score
    };

    std::sort(
        scores.begin(),
        scores.end(),
        std::greater<double>()
    );

    return scores[0] - scores[1];
}

bool detect_code_switch(
    int english_unique_score,
    int filipino_unique_score,
    int bisaya_unique_score
) {
    int language_count = 0;

    if (
        english_unique_score >= 1
    ) {
        language_count++;
    }

    if (
        filipino_unique_score >= 1
    ) {
        language_count++;
    }

    if (
        bisaya_unique_score >= 1
    ) {
        language_count++;
    }

    return language_count >= 2;
}

std::string word_language(
    const std::string& word,
    const std::set<std::string>& english_vocabulary,
    const std::set<std::string>& filipino_vocabulary,
    const std::set<std::string>& bisaya_vocabulary,
    const std::map<std::string, double>& english_profile,
    const std::map<std::string, double>& filipino_profile,
    const std::map<std::string, double>& bisaya_profile
) {
    bool english =
        english_vocabulary.find(word)
        != english_vocabulary.end();

    bool filipino =
        filipino_vocabulary.find(word)
        != filipino_vocabulary.end();

    bool bisaya =
        bisaya_vocabulary.find(word)
        != bisaya_vocabulary.end();

    int matches =
        static_cast<int>(english) +
        static_cast<int>(filipino) +
        static_cast<int>(bisaya);

    if (matches == 1) {
        if (english) {
            return "english";
        }

        if (filipino) {
            return "filipino";
        }

        return "bisaya";
    }

    std::vector<std::string> trigrams =
        build_trigrams(word);

    if (trigrams.empty()) {
        return "unknown";
    }

    double english_score =
        calculate_trigram_score(
            trigrams,
            english_profile
        );

    double filipino_score =
        calculate_trigram_score(
            trigrams,
            filipino_profile
        );

    double bisaya_score =
        calculate_trigram_score(
            trigrams,
            bisaya_profile
        );

    double highest_score =
        std::max({
            english_score,
            filipino_score,
            bisaya_score
        });

    if (highest_score <= 0.0) {
        return "unknown";
    }

    double second_highest_score =
        0.0;

    std::vector<double> scores = {
        english_score,
        filipino_score,
        bisaya_score
    };

    std::sort(
        scores.begin(),
        scores.end(),
        std::greater<double>()
    );

    second_highest_score =
        scores[1];

    double relative_margin =
        highest_score > 0.0
            ? (
                highest_score -
                second_highest_score
            ) / highest_score
            : 0.0;

    const double minimum_confidence =
        0.20;

    const double minimum_margin =
        0.10;

    double confidence =
        highest_score /
        (
            english_score +
            filipino_score +
            bisaya_score
        );

    if (
        confidence < minimum_confidence ||
        relative_margin < minimum_margin
    ) {
        return "shared";
    }

    if (
        english_score >= filipino_score &&
        english_score >= bisaya_score
    ) {
        return "english";
    }

    if (
        filipino_score >= english_score &&
        filipino_score >= bisaya_score
    ) {
        return "filipino";
    }

    return "bisaya";
}

std::vector<LanguageSegment> build_language_segments(
    const std::vector<std::string>& words,
    const std::set<std::string>& english_vocabulary,
    const std::set<std::string>& filipino_vocabulary,
    const std::set<std::string>& bisaya_vocabulary,
    const std::map<std::string, double>& english_profile,
    const std::map<std::string, double>& filipino_profile,
    const std::map<std::string, double>& bisaya_profile
) {
    std::vector<LanguageSegment> segments;

    std::string current_language;
    std::vector<std::string> current_words;

    for (
        const std::string& word :
        words
    ) {
        std::string language =
            word_language(
                word,
                english_vocabulary,
                filipino_vocabulary,
                bisaya_vocabulary,
                english_profile,
                filipino_profile,
                bisaya_profile
            );

        if (
            language == "unknown" ||
            language == "shared"
        ) {
            continue;
        }

        if (
            current_language.empty()
        ) {
            current_language =
                language;

            current_words.clear();
            current_words.push_back(word);

            continue;
        }

        if (
            language == current_language
        ) {
            current_words.push_back(word);

            continue;
        }

        if (
            !current_words.empty()
        ) {
            segments.push_back({
                current_language,
                current_words
            });
        }

        current_language =
            language;

        current_words.clear();
        current_words.push_back(word);
    }

    if (
        !current_words.empty()
    ) {
        segments.push_back({
            current_language,
            current_words
        });
    }

    return segments;
}

int count_language_switches(
    const std::vector<LanguageSegment>& segments
) {
    if (
        segments.size() < 2
    ) {
        return 0;
    }

    return static_cast<int>(
        segments.size() - 1
    );
}

std::string build_switch_direction(
    const std::vector<LanguageSegment>& segments
) {
    if (
        segments.size() < 2
    ) {
        return "";
    }

    std::string result;

    for (
        std::size_t i = 0;
        i < segments.size();
        ++i
    ) {
        if (i > 0) {
            result += "->";
        }

        result +=
            segments[i].language;
    }

    return result;
}

std::string escape_json(
    const std::string& text
) {
    std::string result;

    for (char c : text) {
        if (c == '"') {
            result += "\\\"";
        }
        else if (c == '\\') {
            result += "\\\\";
        }
        else {
            result += c;
        }
    }

    return result;
}

void print_json(
    const std::string& language,
    bool mixed,
    bool code_switched,
    bool ambiguous,
    double confidence,
    double score_margin,
    int switch_count,
    const std::string& code_switch_direction,
    int english_word_score,
    int filipino_word_score,
    int bisaya_word_score,
    int english_unique_score,
    int filipino_unique_score,
    int bisaya_unique_score,
    double english_trigram_score,
    double filipino_trigram_score,
    double bisaya_trigram_score,
    const std::vector<LanguageSegment>& segments
) {
    std::cout
        << "{\n"
        << "  \"language\": \""
        << language
        << "\",\n"
        << "  \"mixed\": "
        << (mixed ? "true" : "false")
        << ",\n"
        << "  \"code_switched\": "
        << (code_switched ? "true" : "false")
        << ",\n"
        << "  \"ambiguous\": "
        << (ambiguous ? "true" : "false")
        << ",\n"
        << "  \"confidence\": "
        << confidence
        << ",\n"
        << "  \"score_margin\": "
        << score_margin
        << ",\n"
        << "  \"switch_count\": "
        << switch_count
        << ",\n"
        << "  \"code_switch_direction\": \""
        << escape_json(
            code_switch_direction
        )
        << "\",\n"
        << "  \"english_word_score\": "
        << english_word_score
        << ",\n"
        << "  \"filipino_word_score\": "
        << filipino_word_score
        << ",\n"
        << "  \"bisaya_word_score\": "
        << bisaya_word_score
        << ",\n"
        << "  \"english_unique_score\": "
        << english_unique_score
        << ",\n"
        << "  \"filipino_unique_score\": "
        << filipino_unique_score
        << ",\n"
        << "  \"bisaya_unique_score\": "
        << bisaya_unique_score
        << ",\n"
        << "  \"english_trigram_score\": "
        << english_trigram_score
        << ",\n"
        << "  \"filipino_trigram_score\": "
        << filipino_trigram_score
        << ",\n"
        << "  \"bisaya_trigram_score\": "
        << bisaya_trigram_score
        << ",\n"
        << "  \"segments\": [\n";

    for (
        std::size_t i = 0;
        i < segments.size();
        ++i
    ) {
        std::cout
            << "    {\n"
            << "      \"language\": \""
            << segments[i].language
            << "\",\n"
            << "      \"words\": \"";

        for (
            std::size_t j = 0;
            j < segments[i].words.size();
            ++j
        ) {
            if (j > 0) {
                std::cout << " ";
            }

            std::cout
                << escape_json(
                    segments[i].words[j]
                );
        }

        std::cout
            << "\"\n"
            << "    }";

        if (
            i + 1 < segments.size()
        ) {
            std::cout << ",";
        }

        std::cout << "\n";
    }

    std::cout
        << "  ]\n"
        << "}"
        << std::endl;
}

int main() {
    const std::string training_directory =
        "training/";

    const std::string english_file =
        training_directory +
        "english.txt";

    const std::string filipino_file =
        training_directory +
        "filipino.txt";

    const std::string bisaya_file =
        training_directory +
        "bisaya.txt";

    std::map<std::string, int> english_profile =
        build_profile(
            english_file
        );

    std::map<std::string, int> filipino_profile =
        build_profile(
            filipino_file
        );

    std::map<std::string, int> bisaya_profile =
        build_profile(
            bisaya_file
        );

    std::map<std::string, double> normalized_english_profile =
        normalize_profile(
            english_profile
        );

    std::map<std::string, double> normalized_filipino_profile =
        normalize_profile(
            filipino_profile
        );

    std::map<std::string, double> normalized_bisaya_profile =
        normalize_profile(
            bisaya_profile
        );

    std::set<std::string> english_vocabulary =
        build_vocabulary(
            english_file
        );

    std::set<std::string> filipino_vocabulary =
        build_vocabulary(
            filipino_file
        );

    std::set<std::string> bisaya_vocabulary =
        build_vocabulary(
            bisaya_file
        );

    std::cout
        << "Quasar Language Engine v0.7.1.1"
        << std::endl;

    std::cout
        << "English trigrams: "
        << english_profile.size()
        << std::endl;

    std::cout
        << "Filipino trigrams: "
        << filipino_profile.size()
        << std::endl;

    std::cout
        << "Bisaya trigrams: "
        << bisaya_profile.size()
        << std::endl;

    std::cout
        << "English vocabulary: "
        << english_vocabulary.size()
        << std::endl;

    std::cout
        << "Filipino vocabulary: "
        << filipino_vocabulary.size()
        << std::endl;

    std::cout
        << "Bisaya vocabulary: "
        << bisaya_vocabulary.size()
        << std::endl;

    while (true) {
        std::cout
            << "\nEnter a message: ";

        std::string message;

        if (
            !std::getline(
                std::cin,
                message
            )
        ) {
            break;
        }

        if (
            message.empty()
        ) {
            continue;
        }

        std::vector<std::string> words =
            tokenize(message);

        int english_word_score =
            count_vocabulary_matches(
                words,
                english_vocabulary
            );

        int filipino_word_score =
            count_vocabulary_matches(
                words,
                filipino_vocabulary
            );

        int bisaya_word_score =
            count_vocabulary_matches(
                words,
                bisaya_vocabulary
            );

        int english_unique_score =
            count_unique_vocabulary_matches(
                words,
                english_vocabulary,
                filipino_vocabulary,
                bisaya_vocabulary
            );

        int filipino_unique_score =
            count_unique_vocabulary_matches(
                words,
                filipino_vocabulary,
                english_vocabulary,
                bisaya_vocabulary
            );

        int bisaya_unique_score =
            count_unique_vocabulary_matches(
                words,
                bisaya_vocabulary,
                english_vocabulary,
                filipino_vocabulary
            );

        std::vector<std::string> trigrams =
            build_trigrams(message);

        double english_trigram_score =
            calculate_trigram_score(
                trigrams,
                normalized_english_profile
            );

        double filipino_trigram_score =
            calculate_trigram_score(
                trigrams,
                normalized_filipino_profile
            );

        double bisaya_trigram_score =
            calculate_trigram_score(
                trigrams,
                normalized_bisaya_profile
            );

        double english_total =
            static_cast<double>(
                english_unique_score
            ) +
            english_trigram_score;

        double filipino_total =
            static_cast<double>(
                filipino_unique_score
            ) +
            filipino_trigram_score;

        double bisaya_total =
            static_cast<double>(
                bisaya_unique_score
            ) +
            bisaya_trigram_score;

        double total_score =
            english_total +
            filipino_total +
            bisaya_total;

        double score_margin =
            calculate_score_margin(
                english_total,
                filipino_total,
                bisaya_total
            );

        const double ambiguity_threshold =
            0.1;

        std::string language =
            "unknown";

        bool mixed = false;
        bool ambiguous = false;

        double confidence = 0.0;

        int strong_language_count = 0;

        if (
            english_word_score >= 2
        ) {
            strong_language_count++;
        }

        if (
            filipino_word_score >= 2
        ) {
            strong_language_count++;
        }

        if (
            bisaya_word_score >= 2
        ) {
            strong_language_count++;
        }

        if (
            strong_language_count < 2
        ) {
            if (
                english_word_score >= 1 &&
                filipino_word_score >= 1
            ) {
                strong_language_count = 2;
            }

            if (
                english_word_score >= 1 &&
                bisaya_word_score >= 1
            ) {
                strong_language_count = 2;
            }

            if (
                filipino_word_score >= 1 &&
                bisaya_word_score >= 1
            ) {
                strong_language_count = 2;
            }
        }

        if (
            strong_language_count >= 2
        ) {
            mixed = true;

            if (
                english_total >= filipino_total &&
                english_total >= bisaya_total
            ) {
                language = "taglish";
            }
            else if (
                filipino_total >= english_total &&
                filipino_total >= bisaya_total
            ) {
                language = "taglish";
            }
            else {
                language = "mixed";
            }

            double highest_score =
                std::max({
                    english_total,
                    filipino_total,
                    bisaya_total
                });

            if (
                total_score > 0.0
            ) {
                confidence =
                    highest_score /
                    total_score;
            }
        }
        else if (
            total_score > 0.0
        ) {
            if (
                score_margin <
                ambiguity_threshold
            ) {
                language = "ambiguous";
                ambiguous = true;
            }
            else if (
                english_total >= filipino_total &&
                english_total >= bisaya_total
            ) {
                language = "english";
            }
            else if (
                filipino_total >= english_total &&
                filipino_total >= bisaya_total
            ) {
                language = "filipino";
            }
            else {
                language = "bisaya";
            }

            double highest_score =
                std::max({
                    english_total,
                    filipino_total,
                    bisaya_total
                });

            confidence =
                highest_score /
                total_score;
        }

        bool code_switched =
            detect_code_switch(
                english_unique_score,
                filipino_unique_score,
                bisaya_unique_score
            );

        std::vector<LanguageSegment> segments =
            build_language_segments(
                words,
                english_vocabulary,
                filipino_vocabulary,
                bisaya_vocabulary,
                normalized_english_profile,
                normalized_filipino_profile,
                normalized_bisaya_profile
            );

        int switch_count =
            count_language_switches(
                segments
            );

        std::string code_switch_direction =
            build_switch_direction(
                segments
            );

        print_json(
            language,
            mixed,
            code_switched,
            ambiguous,
            confidence,
            score_margin,
            switch_count,
            code_switch_direction,
            english_word_score,
            filipino_word_score,
            bisaya_word_score,
            english_unique_score,
            filipino_unique_score,
            bisaya_unique_score,
            english_trigram_score,
            filipino_trigram_score,
            bisaya_trigram_score,
            segments
        );
    }

    return 0;
}