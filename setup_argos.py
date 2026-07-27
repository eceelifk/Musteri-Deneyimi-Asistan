import argostranslate.package
import argostranslate.translate

print("Updating Argos Translate package index...")
argostranslate.package.update_package_index()

available_packages = argostranslate.package.get_available_packages()

print("Looking for English -> Turkish package...")
en_tr_package = next(
    filter(
        lambda x: x.from_code == 'en' and x.to_code == 'tr', available_packages
    )
)
print("Downloading English -> Turkish...")
argostranslate.package.install_from_path(en_tr_package.download())
print("Installed English -> Turkish!")

print("Looking for Turkish -> English package...")
tr_en_package = next(
    filter(
        lambda x: x.from_code == 'tr' and x.to_code == 'en', available_packages
    )
)
print("Downloading Turkish -> English...")
argostranslate.package.install_from_path(tr_en_package.download())
print("Installed Turkish -> English!")

print("Done! Argos Translate is ready.")
