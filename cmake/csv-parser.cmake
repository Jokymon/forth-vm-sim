CPMAddPackage(
    NAME csv
    GIT_TAG "2.1.3"
    GITHUB_REPOSITORY vincentlaucsb/csv-parser
    DOWNLOAD_ONLY
)

if (csv_ADDED)
    add_library(custom_csv INTERFACE)

    target_include_directories(custom_csv
        INTERFACE
            $<BUILD_INTERFACE:${csv_SOURCE_DIR}/single_include>
    )
endif()